"""
Passada ÚNICA de GPU para as features CLIP do Estágio A (Família 4).

Embute com CLIP ViT-B/32 (openai/clip-vit-base-patch32, via
`transformers` -- já presente no Colab, sem instalação nova):
1. TODO o pool de crops das 4 fontes (~86 mil) -- RGB retangular original
   (alpha descartado), ver docstring de src/attribution/clip_features.py.
2. Os objetos REAIS do split de validação do CITRA-3D-Real (~1.267),
   recortados retangularmente pela caixa anotada.

Salva embeddings (.npy) + índice + metadados no Drive, e calcula em CPU:
`dist_clip_alvo` e `novidade_pool` (+ fonte do vizinho mais próximo) por
crop, num CSV. A partir daí, tudo é CPU.

Custo estimado: ~87 mil imagens pequenas por um ViT-B/32 em A100 --
poucos minutos de GPU; a leitura dos PNGs em CPU pode dominar.

Uso no Colab (GPU):

    import sys
    sys.path.insert(0, "/content/synth-detection-attribution")
    from scripts.extrair_clip_estagio_a import main

    main()
"""
from __future__ import annotations

import csv
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image

from src.attribution.clip_features import normalizar_l2, dist_clip_alvo, novidade_pool

RAIZ = "/content/drive/MyDrive/PROJETO_MARINHA/EXPERIMENTO_ATRIBUICAO_CAUSAL"
ZIPS_CROPS = {
    "SMD": f"{RAIZ}/crops_sam3/smd.zip",
    "SeaShips": f"{RAIZ}/crops_sam3/seaships.zip",
    "ABOShips": f"{RAIZ}/crops_sam3/aboships.zip",
    "InaTechShips": f"{RAIZ}/crops_sam3/inatechships.zip",
}
REAL_VAL_IMAGES = "/content/drive/MyDrive/PROJETO_MARINHA/Datasets/CITRA-3D-Real/val/images"
REAL_VAL_LABELS = "/content/drive/MyDrive/PROJETO_MARINHA/Datasets/CITRA-3D-Real/val/labels_final"
DESTINO_DRIVE = f"{RAIZ}/estagio_a/clip"

MODELO_CLIP = "openai/clip-vit-base-patch32"
EXTENSOES_IMG = (".jpg", ".jpeg", ".png")


def _carregar_rgb(caminho: Path) -> Image.Image:
    with Image.open(caminho) as img:
        return img.convert("RGB")  # descarta alpha: retângulo original com fundo


def _recortes_reais(pasta_imagens: Path, pasta_labels: Path) -> tuple[list[Image.Image], list[str]]:
    """Recorta cada caixa anotada (YOLO normalizado) das imagens reais."""
    recortes, ids = [], []
    for label in sorted(pasta_labels.glob("*.txt")):
        candidatos = [pasta_imagens / f"{label.stem}{ext}" for ext in EXTENSOES_IMG]
        caminho_img = next((c for c in candidatos if c.exists()), None)
        if caminho_img is None:
            continue
        img = _carregar_rgb(caminho_img)
        W, H = img.size
        for k, linha in enumerate(label.read_text(encoding="utf-8").splitlines()):
            partes = linha.split()
            if len(partes) < 5:
                continue
            _, cx, cy, w, h = map(float, partes[:5])
            x0 = max(0, int((cx - w / 2) * W)); x1 = min(W, int((cx + w / 2) * W))
            y0 = max(0, int((cy - h / 2) * H)); y1 = min(H, int((cy + h / 2) * H))
            if x1 - x0 < 2 or y1 - y0 < 2:
                continue
            recortes.append(img.crop((x0, y0, x1, y1)))
            ids.append(f"{label.stem}__{k}")
    return recortes, ids


def _tensor_de_features(saida):
    """`get_image_features` retorna um tensor em versões antigas do
    transformers e um objeto de saída em versões recentes. Extrai o
    tensor em ambos os casos, preferindo o embedding PROJETADO (espaço
    conjunto do CLIP, 512-d) quando disponível."""
    import torch
    if isinstance(saida, torch.Tensor):
        return saida
    for atributo in ("image_embeds", "pooler_output", "last_hidden_state"):
        valor = getattr(saida, atributo, None)
        if isinstance(valor, torch.Tensor):
            if atributo == "last_hidden_state":
                valor = valor[:, 0]  # token [CLS]
            return valor
    if isinstance(saida, (tuple, list)) and len(saida) > 0:
        return saida[0]
    raise TypeError(f"Não sei extrair o tensor de {type(saida)}")


def _embutir(imagens: list, model, processor, device, batch: int = 256) -> np.ndarray:
    import torch
    saidas = []
    with torch.no_grad():
        for i in range(0, len(imagens), batch):
            lote = [im if isinstance(im, Image.Image) else _carregar_rgb(im) for im in imagens[i:i + batch]]
            entradas = processor(images=lote, return_tensors="pt").to(device)
            feats = _tensor_de_features(model.get_image_features(**entradas))
            saidas.append(feats.float().cpu().numpy())
            if (i // batch) % 20 == 0:
                print(f"     {min(i + batch, len(imagens))}/{len(imagens)}")
    return normalizar_l2(np.concatenate(saidas, axis=0))


def main(
    zips_crops: dict[str, str] | None = None,
    real_val_images: str = REAL_VAL_IMAGES,
    real_val_labels: str = REAL_VAL_LABELS,
    destino_local: str = "/content/clip_local",
    destino_drive: str = DESTINO_DRIVE,
    batch: int = 256,
) -> dict:
    import torch
    from transformers import CLIPModel, CLIPProcessor

    zips_crops = zips_crops or ZIPS_CROPS
    destino_local = Path(destino_local)
    destino_drive = Path(destino_drive)
    destino_drive.mkdir(parents=True, exist_ok=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Dispositivo: {device}")

    print("\n1) Extraindo os zips de crop e indexando o pool...")
    caminhos, nomes, fontes = [], [], []
    for fonte, zip_path in zips_crops.items():
        pasta = destino_local / "crops" / fonte
        pasta.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(pasta)
        arquivos = sorted(p for p in pasta.iterdir() if p.is_file())
        caminhos += arquivos; nomes += [p.name for p in arquivos]; fontes += [fonte] * len(arquivos)
        print(f"   {fonte}: {len(arquivos)} crops")
    print(f"   Pool total: {len(caminhos)} crops")

    print("\n2) Recortando os objetos reais do alvo (val)...")
    recortes_reais, ids_reais = _recortes_reais(Path(real_val_images), Path(real_val_labels))
    print(f"   {len(recortes_reais)} objetos reais")
    if len(recortes_reais) == 0:
        raise RuntimeError("Nenhum objeto real recortado -- verifique os caminhos de imagens/labels de val.")

    print(f"\n3) Carregando CLIP ({MODELO_CLIP})...")
    model = CLIPModel.from_pretrained(MODELO_CLIP).to(device).eval()
    processor = CLIPProcessor.from_pretrained(MODELO_CLIP)

    inicio = datetime.now(timezone.utc)
    print("\n4) Embutindo o pool (única etapa pesada de GPU)...")
    emb_pool = _embutir(caminhos, model, processor, device, batch)
    print("\n5) Embutindo os objetos reais...")
    emb_real = _embutir(recortes_reais, model, processor, device, batch)
    segundos_gpu = (datetime.now(timezone.utc) - inicio).total_seconds()
    print(f"   GPU concluída em {segundos_gpu:.0f}s. A partir daqui, CPU.")

    print("\n6) Features (CPU): dist_clip_alvo e novidade_pool...")
    dist = dist_clip_alvo(emb_pool, emb_real)
    nov, viz = novidade_pool(emb_pool)

    np.save(destino_drive / "emb_pool.npy", emb_pool)
    np.save(destino_drive / "emb_real_val.npy", emb_real)
    with open(destino_drive / "indice_real_val.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["id_objeto_real"]); w.writerows([[i] for i in ids_reais])
    with open(destino_drive / "features_clip_pool.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["crop_nome", "fonte", "dist_clip_alvo", "novidade_pool", "vizinho_nome", "vizinho_fonte"])
        for i in range(len(nomes)):
            w.writerow([nomes[i], fontes[i], f"{dist[i]:.6f}", f"{nov[i]:.6f}", nomes[viz[i]], fontes[viz[i]]])

    resumo = {
        "gerado_em_utc": datetime.now(timezone.utc).isoformat(),
        "modelo_clip": MODELO_CLIP,
        "representacao": "RGB retangular original (alpha descartado) para pool; recorte retangular da caixa para reais",
        "n_pool": int(len(nomes)), "n_reais_val": int(len(ids_reais)),
        "dim_embedding": int(emb_pool.shape[1]),
        "segundos_gpu": segundos_gpu,
        "dist_clip_alvo": {"media": float(dist.mean()), "mediana": float(np.median(dist)),
                            "p05": float(np.percentile(dist, 5)), "p95": float(np.percentile(dist, 95))},
        "novidade_pool": {"media": float(nov.mean()), "mediana": float(np.median(nov)),
                           "p05": float(np.percentile(nov, 5)), "p95": float(np.percentile(nov, 95))},
        "fracao_vizinho_mesma_fonte": float(np.mean([fontes[i] == fontes[viz[i]] for i in range(len(nomes))])),
    }
    (destino_drive / "metadata_clip.json").write_text(json.dumps(resumo, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n✅ Salvo em {destino_drive}")
    print(json.dumps({k: v for k, v in resumo.items() if k != "gerado_em_utc"}, indent=2, ensure_ascii=False))
    return resumo


if __name__ == "__main__":
    main()

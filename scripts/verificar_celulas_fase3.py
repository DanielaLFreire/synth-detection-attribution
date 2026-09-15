"""
Tarefa 3.2 (Fase 3) -- verificador de viabilidade das células. CPU pura.

1. Lê os manifestos de extração das 3 fontes elegíveis (SMD, SeaShips,
   ABOShips), aplica o filtro do projeto (min_dim_px=20).
2. Calcula o contraste (SÓ sobre a máscara, src/attribution/features.py)
   de TODO o pool elegível -- cacheado no Drive, feito uma vez.
3. Fixa a mediana de contraste do pool elegível (define alto/baixo).
4. Lê as caixas do split de TREINO do CITRA (mesmo conversor px do
   compositor, src/compose/compose.py::ler_caixas_yolo) e verifica a
   viabilidade de cada uma nas 6 células.
5. Gera `configs/celulas_fase3.json` (resumo, gerado por script -- não é
   editado à mão, exigência do adendo §2) e `caixas_viaveis_fase3.csv`.

Os números impressos ao final decidem se o desenho se sustenta ANTES da
primeira hora de GPU.

Uso no Colab (CPU):

    import sys
    sys.path.insert(0, "/content/synth-detection-attribution")
    from scripts.verificar_celulas_fase3 import main

    main()
"""
from __future__ import annotations

import csv
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

from src.attribution.features import calcular_features_intrinsecas
from src.compose.compose import ler_caixas_yolo
from src.factorial import (
    CropElegivel, CaixaAlvo, verificar_viabilidade, comparar_geometria, FONTES_ELEGIVEIS, area_letterbox_640,
)

RAIZ = "/content/drive/MyDrive/PROJETO_MARINHA/EXPERIMENTO_ATRIBUICAO_CAUSAL"
FONTES = {
    "SMD": (f"{RAIZ}/crops_sam3/smd.zip", f"{RAIZ}/crops_sam3/manifesto_extracao_bruta_smd.csv"),
    "SeaShips": (f"{RAIZ}/crops_sam3/seaships.zip", f"{RAIZ}/crops_sam3/manifesto_extracao_bruta_seaships.csv"),
    "ABOShips": (f"{RAIZ}/crops_sam3/aboships.zip", f"{RAIZ}/crops_sam3/manifesto_extracao_bruta_aboships.csv"),
}
REAL_TRAIN_IMAGES = "/content/drive/MyDrive/PROJETO_MARINHA/Datasets/CITRA-3D-Real/train/images"
REAL_TRAIN_LABELS = "/content/drive/MyDrive/PROJETO_MARINHA/Datasets/CITRA-3D-Real/train/labels_final"
CACHE_CONTRASTE = f"{RAIZ}/fase3/contraste_pool_elegivel.csv"
DESTINO_DRIVE = f"{RAIZ}/fase3"
MIN_DIM_PX = 20
EXTENSOES_IMG = (".jpg", ".jpeg", ".png")


def _ler_manifesto(caminho: Path) -> list[dict]:
    with open(caminho, newline="", encoding="utf-8") as f:
        return [l for l in csv.DictReader(f) if l.get("extraido", "True").lower() in ("true", "1", "")]


def _contraste_do_pool(fontes: dict, destino_local: Path, cache: Path) -> dict[str, dict]:
    """{nome_crop: {fonte, largura, altura, contraste}} -- calcula e cacheia."""
    if cache.exists():
        print(f"   cache encontrado: {cache.name}")
        with open(cache, newline="", encoding="utf-8") as f:
            return {l["nome"]: {"fonte": l["fonte"], "largura": int(l["largura"]), "altura": int(l["altura"]),
                                "contraste": float(l["contraste"])} for l in csv.DictReader(f)}

    registros: dict[str, dict] = {}
    for fonte, (zip_path, manifesto) in fontes.items():
        pasta = destino_local / fonte
        pasta.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(pasta)
        linhas = _ler_manifesto(Path(manifesto))
        n_ok = 0
        for l in linhas:
            largura, altura = int(l["largura_px"]), int(l["altura_px"])
            if min(largura, altura) < MIN_DIM_PX:
                continue
            nome = Path(l["caminho_crop"]).name
            caminho = pasta / nome
            if not caminho.exists():
                continue
            feats = calcular_features_intrinsecas(caminho)
            if feats["contraste"] != feats["contraste"]:  # NaN
                continue
            registros[nome] = {"fonte": fonte, "largura": largura, "altura": altura, "contraste": float(feats["contraste"])}
            n_ok += 1
            if n_ok % 5000 == 0:
                print(f"     {fonte}: {n_ok} crops...")
        print(f"   {fonte}: {n_ok} crops elegíveis (min_dim_px={MIN_DIM_PX}) com contraste")

    cache.parent.mkdir(parents=True, exist_ok=True)
    with open(cache, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["nome", "fonte", "largura", "altura", "contraste"])
        for nome, r in registros.items():
            w.writerow([nome, r["fonte"], r["largura"], r["altura"], f"{r['contraste']:.4f}"])
    return registros


def _caixas_de_treino(pasta_imagens: Path, pasta_labels: Path) -> list[CaixaAlvo]:
    caixas = []
    for label in sorted(pasta_labels.glob("*.txt")):
        img = next((pasta_imagens / f"{label.stem}{e}" for e in EXTENSOES_IMG if (pasta_imagens / f"{label.stem}{e}").exists()), None)
        if img is None:
            continue
        with Image.open(img) as im:
            W, H = im.size  # só o cabeçalho, sem decodificar
        for c in ler_caixas_yolo(label, W, H):
            area = float(max(c.largura, 1) * max(c.altura, 1))
            caixas.append(CaixaAlvo(label.stem, c.box_index, area, area_letterbox_640(area, W, H)))
    return caixas


def main(
    fontes: dict | None = None,
    real_train_images: str = REAL_TRAIN_IMAGES,
    real_train_labels: str = REAL_TRAIN_LABELS,
    destino_local: str = "/content/fase3_local",
    destino_drive: str = DESTINO_DRIVE,
    cache_contraste: str = CACHE_CONTRASTE,
    minimo_por_fonte: int = 1,
    niveis_escala: list[str] | None = None,
    sufixo: str = "",
) -> dict:
    fontes = fontes or FONTES
    destino_local = Path(destino_local); destino_drive = Path(destino_drive)
    destino_drive.mkdir(parents=True, exist_ok=True)

    print("1) Contraste de todo o pool elegível (3 fontes)...")
    registros = _contraste_do_pool(fontes, destino_local / "crops", Path(cache_contraste))
    pool = [CropElegivel(n, r["fonte"], float(r["largura"] * r["altura"]), r["contraste"]) for n, r in registros.items()]
    print(f"   pool elegível: {len(pool)} crops\n")

    print("2) Caixas do split de treino...")
    caixas = _caixas_de_treino(Path(real_train_images), Path(real_train_labels))
    n_imgs = len({c.imagem_id for c in caixas})
    print(f"   {len(caixas)} caixas em {n_imgs} imagens\n")

    print(f"3) Viabilidade nas 6 células (mínimo {minimo_por_fonte} crop por fonte por célula)...")
    r = verificar_viabilidade(caixas, pool, minimo_por_fonte=minimo_por_fonte, niveis_escala=niveis_escala)
    geo = comparar_geometria(r.caixas_viaveis, r.caixas_excluidas)

    print(f"\n   mediana de contraste (define alto/baixo): {r.mediana_contraste:.3f}")
    print("   pool por (fonte, contraste):", r.pool_por_fonte_contraste)
    print(f"\n   caixas viáveis em TODAS as células: {len(r.caixas_viaveis)} de {r.n_caixas_total} ({100*r.fracao_viavel:.1f}%)")
    print("   viáveis por célula (antes da interseção):")
    for cel, n in r.viaveis_por_celula.items():
        print(f"     {cel:<20} {n:>6}")
    print("   gargalo (menor nº de crops elegíveis para alguma caixa viável), por célula e fonte:")
    for cel, fs in r.gargalo_por_celula_fonte.items():
        print(f"     {cel:<20} " + "  ".join(f"{f}={n}" for f, n in fs.items()))
    print("\n   geometria -- viáveis vs excluídas (referencial letterbox 640, o do detector):")
    for k in ("viaveis", "excluidas"):
        g = geo[k]
        print(f"     {k:<9}: n={g['n']}, lado mediano a 640={g['lado_mediano_640']:.1f} px, fração small(<32px)={g['fracao_small_640']:.3f}, área mediana nativa={g['area_mediana_nativa']:.0f}")

    imgs_viaveis = sorted({c.imagem_id for c in r.caixas_viaveis})
    config = {
        "gerado_em_utc": datetime.now(timezone.utc).isoformat(),
        "gerado_por": "scripts/verificar_celulas_fase3.py (não editar à mão -- adendo §2)",
        "adendo": "docs/pre_registro/adendo_fase3_fatorial.md (commit efd4699)",
        "fontes_elegiveis": FONTES_ELEGIVEIS,
        "niveis_escala": niveis_escala or ["casada", "reduzida", "ampliada"],
        "min_dim_px": MIN_DIM_PX,
        "faixa_casada_fator_reescala": [0.5, 2.0],
        "mediana_contraste": r.mediana_contraste,
        "minimo_por_fonte": minimo_por_fonte,
        "pool_por_fonte_contraste": r.pool_por_fonte_contraste,
        "n_caixas_treino_total": r.n_caixas_total,
        "n_caixas_viaveis": len(r.caixas_viaveis),
        "fracao_viavel": r.fracao_viavel,
        "n_imagens_com_caixa_viavel": len(imgs_viaveis),
        "viaveis_por_celula": r.viaveis_por_celula,
        "gargalo_por_celula_fonte": r.gargalo_por_celula_fonte,
        "geometria_viaveis_vs_excluidas": geo,
        "n_variacoes": 2,
        "n_sinteticas_por_celula_estimado": 2 * len(imgs_viaveis),
    }
    (destino_drive / f"celulas_fase3{sufixo}.json").write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
    with open(destino_drive / f"caixas_viaveis_fase3{sufixo}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["imagem_id", "box_index", "area_px", "area_640_px"])
        w.writerows([[c.imagem_id, c.box_index, f"{c.area_px:.0f}", f"{c.area_640_px:.1f}"] for c in r.caixas_viaveis])
    print(f"\n✅ Salvo em {destino_drive}: celulas_fase3.json, caixas_viaveis_fase3.csv")
    print("   Copie celulas_fase3.json para configs/ no repositório e commite -- é o artefato do adendo §2.")
    return config


if __name__ == "__main__":
    main()

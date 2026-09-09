"""
Script de entrada para a Fase 1: gera as imagens sintéticas de TREINO,
compondo sobre o split de treino do CITRA-3D-Real -- uso legítimo do
`permitir_split_treino=True` (diferente das colagens de sondagem do
Estágio A, que existem justamente para NÃO tocar o treino, §5.2 do plano).

Combina o pool de crops das quatro fontes (SMD, SeaShips, ABOShips,
InaTechShips), já segmentadas com SAM 3 e filtradas em min_dim_px=20.

`n_variacoes=13`: verificado como aplicável neste contexto (não herdado
às cegas) -- ver docs/CHANGELOG_metodologico.md, 2026-09-02. Gera volume
sintético igual a 13x o volume real, permitindo o balanceamento 50/50
real/sintético via construir_trainlist_balanceado(repeat_real=13).

Uso no Colab:

    import sys
    sys.path.insert(0, "/content/synth-detection-attribution")
    from scripts.gerar_sinteticas_treino import main

    main()
"""
from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

from src.compose import compor_dataset
from src.extraction import carregar_pool_de_crops_do_zip

RAIZ_CROPS = "/content/drive/MyDrive/PROJETO_MARINHA/EXPERIMENTO_ATRIBUICAO_CAUSAL/crops_sam3"
CITRA_TRAIN_IMAGENS = "/content/drive/MyDrive/PROJETO_MARINHA/Datasets/CITRA-3D-Real/train/images"
CITRA_TRAIN_LABELS = "/content/drive/MyDrive/PROJETO_MARINHA/Datasets/CITRA-3D-Real/train/labels_final"
DESTINO_DRIVE = "/content/drive/MyDrive/PROJETO_MARINHA/EXPERIMENTO_ATRIBUICAO_CAUSAL/fase1_piloto/sinteticas_treino"

ZIPS_FONTES = {
    "SMD": f"{RAIZ_CROPS}/smd.zip",
    "SeaShips": f"{RAIZ_CROPS}/seaships.zip",
    "ABOShips": f"{RAIZ_CROPS}/aboships.zip",
    "InaTechShips": f"{RAIZ_CROPS}/inatechships.zip",
}


def main(
    destino_extracao_local: str = "/content/sinteticas_treino_local",
    destino_drive: str = DESTINO_DRIVE,
    zips_fontes: dict[str, str] | None = None,
    citra_train_imagens: str = CITRA_TRAIN_IMAGENS,
    citra_train_labels: str = CITRA_TRAIN_LABELS,
    n_variacoes: int = 13,
    seed: int = 42,
) -> int:
    zips_fontes = zips_fontes or ZIPS_FONTES
    destino_extracao_local = Path(destino_extracao_local)
    destino_drive = Path(destino_drive)

    print("1) Extraindo os zips de crop das quatro fontes para pastas locais temporárias...")
    pool_crops = []
    for fonte, caminho_zip in zips_fontes.items():
        destino_local_fonte = destino_extracao_local / "pool" / fonte.lower()
        pool_fonte = carregar_pool_de_crops_do_zip(Path(caminho_zip), fonte=fonte, destino_local=destino_local_fonte)
        pool_crops.extend(pool_fonte)
        print(f"   {fonte}: {len(pool_fonte)} crops carregados.")
    print(f"   Pool combinado: {len(pool_crops)} crops de {len(zips_fontes)} fontes.\n")

    saida_imagens = destino_extracao_local / "sinteticas" / "images"
    saida_labels = destino_extracao_local / "sinteticas" / "labels"
    manifesto_csv = destino_extracao_local / "manifesto_sinteticas_treino.csv"
    manifesto_meta = destino_extracao_local / "manifesto_sinteticas_treino_meta.json"

    print(f"2) Compondo sintéticas de TREINO sobre o CITRA-3D-Real "
          f"(n_variacoes={n_variacoes}, seed={seed})...")
    print("   AVISO: usando permitir_split_treino=True -- uso legítimo aqui (Fase 1, "
          "geração de dado de treino), diferente do Estágio A.")
    n_colagens = compor_dataset(
        imagens_alvo_dir=Path(citra_train_imagens),
        labels_alvo_dir=Path(citra_train_labels),
        pool_crops=pool_crops,
        saida_imagens_dir=saida_imagens,
        saida_labels_dir=saida_labels,
        manifesto_csv=manifesto_csv,
        manifesto_metadata_json=manifesto_meta,
        split="train",
        n_variacoes=n_variacoes,
        seed=seed,
        permitir_split_treino=True,
    )
    n_imagens_sinteticas = len(list(saida_imagens.glob("*.png")))
    print(f"   {n_colagens} colagens geradas (linhas de manifesto).")
    print(f"   {n_imagens_sinteticas} imagens sintéticas de cena completa geradas.\n")

    print(f"3) Compactando imagens e labels, copiando para o Drive ({destino_drive})...")
    destino_drive.mkdir(parents=True, exist_ok=True)

    zip_imagens = destino_extracao_local / "sinteticas_images.zip"
    with zipfile.ZipFile(zip_imagens, "w", zipfile.ZIP_DEFLATED) as zf:
        for caminho in sorted(saida_imagens.glob("*.png")):
            zf.write(caminho, arcname=caminho.name)
    shutil.copy2(zip_imagens, destino_drive / "sinteticas_images.zip")

    zip_labels = destino_extracao_local / "sinteticas_labels.zip"
    with zipfile.ZipFile(zip_labels, "w", zipfile.ZIP_DEFLATED) as zf:
        for caminho in sorted(saida_labels.glob("*.txt")):
            zf.write(caminho, arcname=caminho.name)
    shutil.copy2(zip_labels, destino_drive / "sinteticas_labels.zip")

    shutil.copy2(manifesto_csv, destino_drive / manifesto_csv.name)
    shutil.copy2(manifesto_meta, destino_drive / manifesto_meta.name)

    print(f"\n✅ Concluído. {n_imagens_sinteticas} imagens sintéticas de treino geradas "
          f"({n_colagens} colagens).")
    print(f"   Imagens: {destino_drive / 'sinteticas_images.zip'}")
    print(f"   Labels: {destino_drive / 'sinteticas_labels.zip'}")
    print(f"   Manifesto: {destino_drive / manifesto_csv.name}")
    print(f"\n   Nota: para usar em treino real, extraia estes dois zips para pastas locais "
          f"antes de chamar construir_trainlist_balanceado (o treino Ultralytics precisa de "
          f"arquivos de imagem/label soltos em disco, não dentro de um zip).")

    return n_imagens_sinteticas


if __name__ == "__main__":
    main()

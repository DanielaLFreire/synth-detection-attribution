"""
Script de entrada para a tarefa -1.6 (InaTechShips, quarta fonte de crop):
extrai o zip, extrai crops a partir da anotação YOLO já em classe única
(labels_single_class/), combinando os três splits (train/val/test) num
único pool -- esta fonte não tem papel de alvo/fundo de composição, só de
fonte de crop, então maximizar volume combinando os splits é seguro (não
há risco de memorização, que só se aplica ao dataset-alvo, ver §5.2).

Nenhum extrator novo foi necessário -- reaproveita extrair_crops_de_yolo,
já usado para SMD e UA-DETRAC.

Uso no Colab:

    import sys
    sys.path.insert(0, "/content/synth-detection-attribution")
    from scripts.extrair_inatechships import main

    main(
        caminho_zip="/content/drive/MyDrive/PROJETO_MARINHA/Datasets/_zips/dataset_25k_v2.zip",
        destino_extracao_local="/content/inatechships_extraido_sam3",
        destino_crops_drive="/content/drive/MyDrive/PROJETO_MARINHA/EXPERIMENTO_ATRIBUICAO_CAUSAL/crops_sam3",
        min_dim_px=20,   # já decidido na tarefa 0.2
        segmentador=segmentador_sam3,
    )
"""
from __future__ import annotations

import argparse
import shutil
import zipfile
from pathlib import Path

from src.extraction import extrair_crops_de_yolo, filtrar_pool_de_crops, FiltroConfig, compactar_arquivos, carregar_coberturas_do_manifesto_extracao
from src.segmentation import Segmentador


def main(
    caminho_zip: str,
    destino_extracao_local: str,
    destino_crops_drive: str,
    min_dim_px: int,
    segmentador: Segmentador | None = None,
) -> None:
    caminho_zip = Path(caminho_zip)
    destino_extracao_local = Path(destino_extracao_local)
    destino_crops_drive = Path(destino_crops_drive)

    print(f"1) Extraindo {caminho_zip.name} para {destino_extracao_local}...")
    destino_extracao_local.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(caminho_zip) as z:
        z.extractall(destino_extracao_local)

    raiz_dataset = destino_extracao_local / "dataset_25k_v2"
    if not raiz_dataset.is_dir():
        raise FileNotFoundError(f"pasta esperada não encontrada em {raiz_dataset}")

    crops_brutos_dir = destino_extracao_local / "crops_brutos_inatechships"
    total_extraidos = 0
    coberturas_combinadas: dict[str, float] = {}

    for i, split in enumerate(("train", "val", "test"), start=1):
        imagens_dir = raiz_dataset / split / "images"
        labels_dir = raiz_dataset / split / "labels_single_class"
        manifesto_split = destino_extracao_local / f"manifesto_extracao_bruta_inatechships_{split}.csv"

        print(f"2.{i}) Extraindo crops do split {split} ({imagens_dir})...")
        extraidos = extrair_crops_de_yolo(
            fonte="InaTechShips",
            imagens_dir=imagens_dir,
            labels_dir=labels_dir,
            saida_crops_dir=crops_brutos_dir,
            manifesto_csv=manifesto_split,
            extensao_imagem=".jpg",
            segmentador=segmentador,
        )
        print(f"    {len(extraidos)} crops extraídos deste split.")
        total_extraidos += len(extraidos)
        coberturas_combinadas.update(carregar_coberturas_do_manifesto_extracao(manifesto_split))

    print(f"\n   Total combinado (train+val+test): {total_extraidos} crops extraídos "
          f"(antes do filtro de qualidade).")

    print(f"3) Aplicando filtro unificado (min_dim_px={min_dim_px})...")
    config = FiltroConfig(min_dim_px=min_dim_px)
    mantidos = filtrar_pool_de_crops(
        fonte="InaTechShips",
        crops_dir=crops_brutos_dir,
        config=config,
        manifesto_csv=destino_extracao_local / "manifesto_filtro_qualidade_inatechships.csv",
        manifesto_metadata_json=destino_extracao_local / "manifesto_filtro_qualidade_inatechships_meta.json",
        coberturas_mascara=coberturas_combinadas,
    )
    print(f"   {len(mantidos)} de {total_extraidos} crops mantidos após o filtro "
          f"({100 * len(mantidos) / max(1, total_extraidos):.1f}% de aproveitamento).")

    print(f"4) Compactando {len(mantidos)} crops mantidos e copiando para o Drive ({destino_crops_drive})...")
    destino_crops_drive.mkdir(parents=True, exist_ok=True)
    caminho_zip_local = destino_extracao_local / "inatechships.zip"
    compactar_arquivos([caminho for _, caminho in mantidos], caminho_zip_local)
    shutil.copy2(caminho_zip_local, destino_crops_drive / "inatechships.zip")

    for split in ("train", "val", "test"):
        shutil.copy2(
            destino_extracao_local / f"manifesto_extracao_bruta_inatechships_{split}.csv",
            destino_crops_drive / f"manifesto_extracao_bruta_inatechships_{split}.csv",
        )
    for nome_manifesto in (
        "manifesto_filtro_qualidade_inatechships.csv",
        "manifesto_filtro_qualidade_inatechships_meta.json",
    ):
        shutil.copy2(destino_extracao_local / nome_manifesto, destino_crops_drive / nome_manifesto)

    print(f"\n✅ Concluído. {len(mantidos)} crops do InaTechShips compactados em "
          f"{destino_crops_drive / 'inatechships.zip'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--caminho-zip", required=True)
    parser.add_argument("--destino-extracao-local", required=True)
    parser.add_argument("--destino-crops-drive", required=True)
    parser.add_argument("--min-dim-px", type=int, required=True)
    args = parser.parse_args()
    main(args.caminho_zip, args.destino_extracao_local, args.destino_crops_drive, args.min_dim_px)

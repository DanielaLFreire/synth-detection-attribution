"""
Script de entrada para a tarefa -1.6 (ABOShips): extrai o zip, extrai os
crops a partir do CSV (imagens indexadas por nome-base entre as 16
subpastas de data), e aplica o filtro unificado (-1.3) em sequência.

Uso no Colab:

    import sys
    sys.path.insert(0, "/content/synth-detection-attribution")
    from scripts.extrair_aboships import main

    main(
        caminho_zip="/content/drive/MyDrive/PROJETO_MARINHA/Datasets/_zips/ABOships.zip",
        destino_extracao_local="/content/aboships_extraido",
        destino_crops_drive="/content/drive/MyDrive/PROJETO_MARINHA/EXPERIMENTO_ATRIBUICAO_CAUSAL/crops",
        min_dim_px=32,   # AJUSTAR conforme decisão da tarefa 0.2
    )
"""
from __future__ import annotations

import argparse
import shutil
import zipfile
from pathlib import Path

from src.extraction import extrair_crops_de_csv_abo, filtrar_pool_de_crops, FiltroConfig
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

    print(f"1) Extraindo {caminho_zip.name} para {destino_extracao_local} (local, não Drive)...")
    destino_extracao_local.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(caminho_zip) as z:
        z.extractall(destino_extracao_local)

    imagens_dir = destino_extracao_local / "ABOshipsDataset" / "Seaships"
    caminho_csv = destino_extracao_local / "ABOshipsDataset" / "Labels" / "Vesibussi_Labels.csv"
    if not imagens_dir.is_dir():
        raise FileNotFoundError(f"pasta de imagens não encontrada em {imagens_dir}")
    if not caminho_csv.exists():
        raise FileNotFoundError(f"CSV de anotação não encontrado em {caminho_csv}")

    print(f"2) Extraindo crops a partir de {caminho_csv.name} "
          f"(indexando imagens em {imagens_dir})...")
    crops_brutos_dir = destino_extracao_local / "crops_brutos_aboships"
    extraidos = extrair_crops_de_csv_abo(
        fonte="ABOShips",
        imagens_dir=imagens_dir,
        caminho_csv=caminho_csv,
        saida_crops_dir=crops_brutos_dir,
        manifesto_csv=destino_extracao_local / "manifesto_extracao_bruta_aboships.csv",
        segmentador=segmentador,
    )
    print(f"   {len(extraidos)} crops extraídos (antes do filtro de qualidade).")

    print(f"3) Aplicando filtro unificado (min_dim_px={min_dim_px})...")
    config = FiltroConfig(min_dim_px=min_dim_px)
    mantidos = filtrar_pool_de_crops(
        fonte="ABOShips",
        crops_dir=crops_brutos_dir,
        config=config,
        manifesto_csv=destino_extracao_local / "manifesto_filtro_qualidade_aboships.csv",
        manifesto_metadata_json=destino_extracao_local / "manifesto_filtro_qualidade_aboships_meta.json",
    )
    print(f"   {len(mantidos)} de {len(extraidos)} crops mantidos após o filtro "
          f"({100 * len(mantidos) / max(1, len(extraidos)):.1f}% de aproveitamento).")

    print(f"4) Copiando crops mantidos e manifestos para o Drive ({destino_crops_drive})...")
    destino_crops_drive.mkdir(parents=True, exist_ok=True)
    destino_aboships_dir = destino_crops_drive / "aboships"
    destino_aboships_dir.mkdir(parents=True, exist_ok=True)
    for _, caminho_crop in mantidos:
        shutil.copy2(caminho_crop, destino_aboships_dir / caminho_crop.name)

    for nome_manifesto in (
        "manifesto_extracao_bruta_aboships.csv",
        "manifesto_filtro_qualidade_aboships.csv",
        "manifesto_filtro_qualidade_aboships_meta.json",
    ):
        shutil.copy2(destino_extracao_local / nome_manifesto, destino_crops_drive / nome_manifesto)

    print(f"\n✅ Concluído. {len(mantidos)} crops do ABOShips prontos em {destino_aboships_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--caminho-zip", required=True)
    parser.add_argument("--destino-extracao-local", required=True)
    parser.add_argument("--destino-crops-drive", required=True)
    parser.add_argument("--min-dim-px", type=int, required=True)
    args = parser.parse_args()
    main(args.caminho_zip, args.destino_extracao_local, args.destino_crops_drive, args.min_dim_px)

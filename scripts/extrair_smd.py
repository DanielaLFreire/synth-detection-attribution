"""
Script de entrada para a tarefa -1.6 (SMD): extrai o zip, extrai os crops
a partir da anotação YOLO, e aplica o filtro unificado (-1.3) em sequência.

Uso no Colab:

    import sys
    sys.path.insert(0, "/content/synth-detection-attribution")
    from scripts.extrair_smd import main

    main(
        caminho_zip="/content/drive/MyDrive/PROJETO_MARINHA/Datasets/_zips/smd_clean.zip",
        destino_extracao_local="/content/smd_extraido",       # local, não Drive -- mais rápido
        destino_crops_drive="/content/drive/MyDrive/PROJETO_MARINHA/EXPERIMENTO_ATRIBUICAO_CAUSAL/crops",
        min_dim_px=32,   # AJUSTAR conforme decisão da tarefa 0.2 -- valor de exemplo aqui
    )

Nota: extrai o zip para um diretório LOCAL do Colab (/content/...), não
direto no Drive -- ler/escrever milhares de arquivos pequenos via FUSE (o
sistema de arquivos do Drive montado) é lento e sujeito a falha parcial,
lição já documentada no projeto anterior. Só o resultado final (crops
filtrados + manifestos) é copiado para o Drive.
"""
from __future__ import annotations

import argparse
import shutil
import zipfile
from pathlib import Path

from src.extraction import extrair_crops_de_yolo, filtrar_pool_de_crops, FiltroConfig


def main(
    caminho_zip: str,
    destino_extracao_local: str,
    destino_crops_drive: str,
    min_dim_px: int,
    split_smd: str = "test",  # ver achado registrado: todo o SMD útil está em test/
) -> None:
    caminho_zip = Path(caminho_zip)
    destino_extracao_local = Path(destino_extracao_local)
    destino_crops_drive = Path(destino_crops_drive)

    print(f"1) Extraindo {caminho_zip.name} para {destino_extracao_local} (local, não Drive)...")
    destino_extracao_local.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(caminho_zip) as z:
        z.extractall(destino_extracao_local)

    imagens_dir = destino_extracao_local / "smd_clean" / split_smd / "images"
    labels_dir = destino_extracao_local / "smd_clean" / split_smd / "labels"
    if not imagens_dir.is_dir():
        raise FileNotFoundError(
            f"pasta de imagens não encontrada em {imagens_dir} -- confirme a "
            "estrutura interna do zip (pode ter mudado desde a última verificação)."
        )

    print(f"2) Extraindo crops a partir da anotação YOLO em {labels_dir}...")
    crops_brutos_dir = destino_extracao_local / "crops_brutos_smd"
    extraidos = extrair_crops_de_yolo(
        fonte="SMD",
        imagens_dir=imagens_dir,
        labels_dir=labels_dir,
        saida_crops_dir=crops_brutos_dir,
        manifesto_csv=destino_extracao_local / "manifesto_extracao_bruta_smd.csv",
    )
    print(f"   {len(extraidos)} crops extraídos (antes do filtro de qualidade).")

    print(f"3) Aplicando filtro unificado (min_dim_px={min_dim_px})...")
    config = FiltroConfig(min_dim_px=min_dim_px)
    mantidos = filtrar_pool_de_crops(
        fonte="SMD",
        crops_dir=crops_brutos_dir,
        config=config,
        manifesto_csv=destino_extracao_local / "manifesto_filtro_qualidade_smd.csv",
        manifesto_metadata_json=destino_extracao_local / "manifesto_filtro_qualidade_smd_meta.json",
    )
    print(f"   {len(mantidos)} de {len(extraidos)} crops mantidos após o filtro "
          f"({100 * len(mantidos) / max(1, len(extraidos)):.1f}% de aproveitamento).")

    print(f"4) Copiando crops mantidos e manifestos para o Drive ({destino_crops_drive})...")
    destino_crops_drive.mkdir(parents=True, exist_ok=True)
    destino_smd_dir = destino_crops_drive / "smd"
    destino_smd_dir.mkdir(parents=True, exist_ok=True)
    for _, caminho_crop in mantidos:
        shutil.copy2(caminho_crop, destino_smd_dir / caminho_crop.name)

    for nome_manifesto in (
        "manifesto_extracao_bruta_smd.csv",
        "manifesto_filtro_qualidade_smd.csv",
        "manifesto_filtro_qualidade_smd_meta.json",
    ):
        shutil.copy2(destino_extracao_local / nome_manifesto, destino_crops_drive / nome_manifesto)

    print(f"\n✅ Concluído. {len(mantidos)} crops do SMD prontos em {destino_smd_dir}")
    print("   Manifestos copiados para o Drive junto com os crops -- auditoria preservada.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--caminho-zip", required=True)
    parser.add_argument("--destino-extracao-local", required=True)
    parser.add_argument("--destino-crops-drive", required=True)
    parser.add_argument("--min-dim-px", type=int, required=True)
    args = parser.parse_args()
    main(args.caminho_zip, args.destino_extracao_local, args.destino_crops_drive, args.min_dim_px)

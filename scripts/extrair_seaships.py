"""
Script de entrada para a tarefa -1.6 (SeaShips): extrai o zip, deduplica as
cópias por augmentation do Roboflow (achado de 2026-08-31 -- 13.105 imagens,
apenas 6.979 bases únicas), extrai os crops a partir da anotação VOC XML, e
aplica o filtro unificado (-1.3) em sequência.

Uso no Colab:

    import sys
    sys.path.insert(0, "/content/synth-detection-attribution")
    from scripts.extrair_seaships import main

    main(
        caminho_zip="/content/drive/MyDrive/PROJETO_MARINHA/Datasets/_zips/SeaShips_voc.zip",
        destino_extracao_local="/content/seaships_extraido",
        destino_crops_drive="/content/drive/MyDrive/PROJETO_MARINHA/EXPERIMENTO_ATRIBUICAO_CAUSAL/crops",
        min_dim_px=32,   # AJUSTAR conforme decisão da tarefa 0.2
    )
"""
from __future__ import annotations

import argparse
import shutil
import zipfile
from pathlib import Path

from src.extraction import (
    deduplicar_por_base,
    extrair_crops_de_voc,
    filtrar_pool_de_crops,
    FiltroConfig,
)
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

    # A estrutura interna do SeaShips_voc.zip mistura imagens e XMLs na
    # mesma pasta (achado de 2026-08-31) -- localizamos dinamicamente em
    # vez de assumir uma estrutura de subpastas fixa.
    todos_arquivos = list(destino_extracao_local.rglob("*"))
    imagens = [p for p in todos_arquivos if p.suffix.lower() in (".jpg", ".jpeg")]
    if not imagens:
        raise FileNotFoundError(f"nenhuma imagem .jpg encontrada em {destino_extracao_local}")
    pasta_dados = imagens[0].parent
    print(f"   Pasta de dados identificada: {pasta_dados} ({len(imagens)} imagens brutas)")

    print("2) Deduplicando cópias por augmentation do Roboflow...")
    resultado_dedup = deduplicar_por_base(imagens)
    print(f"   {len(imagens)} imagens totais -> {resultado_dedup.n_bases_unicas} bases únicas "
          f"({len(resultado_dedup.descartados)} descartadas como duplicata, "
          f"{len(resultado_dedup.sem_padrao_reconhecido)} fora do padrão Roboflow)")

    # move as imagens únicas (+ seus XMLs correspondentes) para uma pasta
    # separada, para que o extrator VOC só veja o conjunto deduplicado
    pasta_dedup_imagens = destino_extracao_local / "dedup" / "images"
    pasta_dedup_anotacoes = destino_extracao_local / "dedup" / "annotations"
    pasta_dedup_imagens.mkdir(parents=True, exist_ok=True)
    pasta_dedup_anotacoes.mkdir(parents=True, exist_ok=True)

    n_sem_xml = 0
    for caminho_img in resultado_dedup.mantidos + resultado_dedup.sem_padrao_reconhecido:
        caminho_xml = caminho_img.with_suffix(".xml")
        if not caminho_xml.exists():
            n_sem_xml += 1
            continue
        shutil.copy2(caminho_img, pasta_dedup_imagens / caminho_img.name)
        shutil.copy2(caminho_xml, pasta_dedup_anotacoes / caminho_xml.name)
    if n_sem_xml:
        print(f"   ⚠️  {n_sem_xml} imagem(ns) únicas sem XML correspondente -- ignoradas nesta etapa.")

    print("3) Extraindo crops a partir da anotação VOC XML (conjunto já deduplicado)...")
    crops_brutos_dir = destino_extracao_local / "crops_brutos_seaships"
    extraidos = extrair_crops_de_voc(
        fonte="SeaShips",
        imagens_dir=pasta_dedup_imagens,
        anotacoes_dir=pasta_dedup_anotacoes,
        saida_crops_dir=crops_brutos_dir,
        manifesto_csv=destino_extracao_local / "manifesto_extracao_bruta_seaships.csv",
        segmentador=segmentador,
    )
    print(f"   {len(extraidos)} crops extraídos (antes do filtro de qualidade).")

    print(f"4) Aplicando filtro unificado (min_dim_px={min_dim_px})...")
    config = FiltroConfig(min_dim_px=min_dim_px)
    mantidos = filtrar_pool_de_crops(
        fonte="SeaShips",
        crops_dir=crops_brutos_dir,
        config=config,
        manifesto_csv=destino_extracao_local / "manifesto_filtro_qualidade_seaships.csv",
        manifesto_metadata_json=destino_extracao_local / "manifesto_filtro_qualidade_seaships_meta.json",
    )
    print(f"   {len(mantidos)} de {len(extraidos)} crops mantidos após o filtro "
          f"({100 * len(mantidos) / max(1, len(extraidos)):.1f}% de aproveitamento).")

    print(f"5) Copiando crops mantidos e manifestos para o Drive ({destino_crops_drive})...")
    destino_crops_drive.mkdir(parents=True, exist_ok=True)
    destino_seaships_dir = destino_crops_drive / "seaships"
    destino_seaships_dir.mkdir(parents=True, exist_ok=True)
    for _, caminho_crop in mantidos:
        shutil.copy2(caminho_crop, destino_seaships_dir / caminho_crop.name)

    for nome_manifesto in (
        "manifesto_extracao_bruta_seaships.csv",
        "manifesto_filtro_qualidade_seaships.csv",
        "manifesto_filtro_qualidade_seaships_meta.json",
    ):
        shutil.copy2(destino_extracao_local / nome_manifesto, destino_crops_drive / nome_manifesto)

    print(f"\n✅ Concluído. {len(mantidos)} crops do SeaShips prontos em {destino_seaships_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--caminho-zip", required=True)
    parser.add_argument("--destino-extracao-local", required=True)
    parser.add_argument("--destino-crops-drive", required=True)
    parser.add_argument("--min-dim-px", type=int, required=True)
    args = parser.parse_args()
    main(args.caminho_zip, args.destino_extracao_local, args.destino_crops_drive, args.min_dim_px)

"""
Script de entrada para a tarefa -1.8: prepara o UA-DETRAC-DATASET-10K como
segundo domínio de validação (§2.3 do plano).

Papéis dos dois splits do zip original, para este projeto:
- train/  -> fonte do banco de recorte de veículos (crops), análogo ao
             papel de ABOShips/InaTechShips/SMD/SeaShips para o CITRA.
- valid/  -> fundo de composição para a réplica do Estágio A (Fase 2.5),
             análogo ao papel do split de validação do CITRA-3D-Real (§5.2:
             nunca usar o split usado para ajustar o detector).

Etapas: (1) extrai o zip, (2) colapsa as 4 classes originais
(bus/car/truck/van) para a classe única `vehicle`, (3) deduplica cópias por
augmentation do Roboflow (achado: 100 de 9.816 imagens no train), (4)
materializa e valida `labels_final/` do split valid (fundo de composição),
(5) extrai o pool de crops de veículo a partir do split train (já
deduplicado e de classe única) e aplica o filtro unificado.

Uso no Colab:

    import sys
    sys.path.insert(0, "/content/synth-detection-attribution")
    from scripts.preparar_ua_detrac import main

    main(
        caminho_zip="/content/drive/MyDrive/PROJETO_MARINHA/Datasets/_zips/UA-DETRAC-DATASET-10K.zip",
        destino_extracao_local="/content/ua_detrac_extraido",
        destino_drive="/content/drive/MyDrive/PROJETO_MARINHA/EXPERIMENTO_ATRIBUICAO_CAUSAL/segundo_dominio_uadetrac",
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
    extrair_crops_de_yolo,
    filtrar_pool_de_crops,
    FiltroConfig,
)
from src.materialize import colapsar_para_classe_unica, materializar_labels_final
from src.segmentation import Segmentador

CLASSES_ORIGINAIS_UA_DETRAC = {"0", "1", "2", "3"}  # bus, car, truck, van (data.yaml verificado)


def main(
    caminho_zip: str,
    destino_extracao_local: str,
    destino_drive: str,
    min_dim_px: int,
    segmentador: Segmentador | None = None,
) -> None:
    caminho_zip = Path(caminho_zip)
    destino_extracao_local = Path(destino_extracao_local)
    destino_drive = Path(destino_drive)

    print(f"1) Extraindo {caminho_zip.name} para {destino_extracao_local}...")
    destino_extracao_local.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(caminho_zip) as z:
        z.extractall(destino_extracao_local)

    print("\n2) Colapsando classes (bus/car/truck/van -> vehicle) em train e valid...")
    for split in ("train", "valid"):
        origem = destino_extracao_local / split / "labels"
        destino = destino_extracao_local / split / "labels_single_class"
        relatorio = colapsar_para_classe_unica(
            labels_origem_dir=origem, labels_destino_dir=destino,
            classes_originais_validas=CLASSES_ORIGINAIS_UA_DETRAC,
        )
        print(f"   {split}: {relatorio.n_arquivos} arquivos, {relatorio.n_linhas} caixas, "
              f"por classe original: {relatorio.contagem_por_classe_original}")

    print("\n3) Deduplicando cópias por augmentation do Roboflow (split train)...")
    imagens_train = list((destino_extracao_local / "train" / "images").glob("*.jpg"))
    resultado_dedup = deduplicar_por_base(imagens_train)
    print(f"   {len(imagens_train)} imagens -> {resultado_dedup.n_bases_unicas} bases únicas "
          f"({len(resultado_dedup.descartados)} descartadas)")

    pasta_train_dedup_imgs = destino_extracao_local / "train_dedup" / "images"
    pasta_train_dedup_labels = destino_extracao_local / "train_dedup" / "labels_single_class"
    pasta_train_dedup_imgs.mkdir(parents=True, exist_ok=True)
    pasta_train_dedup_labels.mkdir(parents=True, exist_ok=True)
    labels_single_class_train = destino_extracao_local / "train" / "labels_single_class"
    for caminho_img in resultado_dedup.mantidos + resultado_dedup.sem_padrao_reconhecido:
        caminho_label = labels_single_class_train / f"{caminho_img.stem}.txt"
        shutil.copy2(caminho_img, pasta_train_dedup_imgs / caminho_img.name)
        if caminho_label.exists():
            shutil.copy2(caminho_label, pasta_train_dedup_labels / caminho_label.name)

    print("\n4) Materializando labels_final/ do split valid (fundo de composição, §5.2)...")
    relatorios = materializar_labels_final(
        root_dataset_alvo=destino_extracao_local,
        labels_subfolder_origem="labels_single_class",
        splits=["valid"],
    )
    for r in relatorios:
        print(f"   {r.split}: {r.n_labels_copiados} labels, {r.n_boxes_total} boxes -- "
              f"manifesto: {r.caminho_manifesto}")

    print(f"\n5) Extraindo pool de crops de veículo a partir do train deduplicado "
          f"(min_dim_px={min_dim_px})...")
    crops_brutos_dir = destino_extracao_local / "crops_brutos_ua_detrac"
    extraidos = extrair_crops_de_yolo(
        fonte="UA-DETRAC",
        imagens_dir=pasta_train_dedup_imgs,
        labels_dir=pasta_train_dedup_labels,
        saida_crops_dir=crops_brutos_dir,
        manifesto_csv=destino_extracao_local / "manifesto_extracao_bruta_ua_detrac.csv",
        extensao_imagem=".jpg",
        segmentador=segmentador,
    )
    print(f"   {len(extraidos)} crops extraídos (antes do filtro de qualidade).")

    config = FiltroConfig(min_dim_px=min_dim_px)
    mantidos = filtrar_pool_de_crops(
        fonte="UA-DETRAC",
        crops_dir=crops_brutos_dir,
        config=config,
        manifesto_csv=destino_extracao_local / "manifesto_filtro_qualidade_ua_detrac.csv",
        manifesto_metadata_json=destino_extracao_local / "manifesto_filtro_qualidade_ua_detrac_meta.json",
    )
    print(f"   {len(mantidos)} de {len(extraidos)} crops mantidos após o filtro "
          f"({100 * len(mantidos) / max(1, len(extraidos)):.1f}% de aproveitamento).")

    print(f"\n6) Copiando pool de crops e fundo de composição (valid) para o Drive ({destino_drive})...")
    destino_drive.mkdir(parents=True, exist_ok=True)
    destino_crops = destino_drive / "crops_veiculos"
    destino_crops.mkdir(parents=True, exist_ok=True)
    for _, caminho_crop in mantidos:
        shutil.copy2(caminho_crop, destino_crops / caminho_crop.name)

    destino_valid = destino_drive / "valid_background"
    shutil.copytree(destino_extracao_local / "valid" / "images", destino_valid / "images", dirs_exist_ok=True)
    shutil.copytree(destino_extracao_local / "valid" / "labels_final", destino_valid / "labels_final", dirs_exist_ok=True)
    shutil.copy2(destino_extracao_local / "valid" / "labels_final_manifest.json", destino_valid / "labels_final_manifest.json")

    print(f"\n✅ Concluído. Pool de {len(mantidos)} crops em {destino_crops}, "
          f"fundo de composição (valid) em {destino_valid}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--caminho-zip", required=True)
    parser.add_argument("--destino-extracao-local", required=True)
    parser.add_argument("--destino-drive", required=True)
    parser.add_argument("--min-dim-px", type=int, required=True)
    args = parser.parse_args()
    main(args.caminho_zip, args.destino_extracao_local, args.destino_drive, args.min_dim_px)

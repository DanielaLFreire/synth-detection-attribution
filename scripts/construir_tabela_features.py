"""
Script de entrada para a Fase 2 (Estágio A): constrói a tabela de
features de CPU a partir do alvo já construído, dos crops (extraídos dos
zips das quatro fontes) e dos labels reais do split de validação do
CITRA-3D-Real (para a regressão de coerência). Nenhuma GPU.

Uso no Colab:

    import sys
    sys.path.insert(0, "/content/synth-detection-attribution")
    from scripts.construir_tabela_features import main

    main()
"""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

from src.attribution import construir_tabela_features, construir_indice_crops

RAIZ = "/content/drive/MyDrive/PROJETO_MARINHA/EXPERIMENTO_ATRIBUICAO_CAUSAL"
ALVO_CSV = f"{RAIZ}/estagio_a/alvo/alvo_iou0.5_conf0.25.csv"
LABELS_REAIS_VAL = "/content/drive/MyDrive/PROJETO_MARINHA/Datasets/CITRA-3D-Real/val/labels_final"
ZIPS_CROPS = [
    f"{RAIZ}/crops_sam3/smd.zip",
    f"{RAIZ}/crops_sam3/seaships.zip",
    f"{RAIZ}/crops_sam3/aboships.zip",
    f"{RAIZ}/crops_sam3/inatechships.zip",
]
DESTINO_DRIVE = f"{RAIZ}/estagio_a/features"


def main(
    alvo_csv: str = ALVO_CSV,
    labels_reais_val: str = LABELS_REAIS_VAL,
    zips_crops: list[str] | None = None,
    destino_local: str = "/content/features_local",
    destino_drive: str = DESTINO_DRIVE,
) -> dict:
    zips_crops = zips_crops or ZIPS_CROPS
    destino_local = Path(destino_local)

    print("1) Extraindo os zips de crop para disco local (necessário para as features intrínsecas)...")
    pastas = []
    for caminho_zip in zips_crops:
        pasta = destino_local / "crops" / Path(caminho_zip).stem
        pasta.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(caminho_zip) as z:
            z.extractall(pasta)
        pastas.append(pasta)
        print(f"   {Path(caminho_zip).name}: {sum(1 for _ in pasta.iterdir())} arquivos")

    indice = construir_indice_crops(pastas)
    print(f"   Índice: {len(indice)} crops únicos localizáveis.\n")

    print("2) Construindo a tabela de features (geometria + coerência + intrínsecas por crop único)...")
    destino_csv = destino_local / "tabela_features_estagio_a.csv"
    resumo = construir_tabela_features(Path(alvo_csv), Path(labels_reais_val), indice, destino_csv)
    print(f"   {resumo['n_linhas']} linhas, {resumo['n_crops_unicos']} crops únicos, "
          f"{resumo['n_crops_nao_localizados']} não localizados")
    print(f"   Regressão de coerência (log área ~ pos_v): a={resumo['regressao_coerencia']['a']:.3f}, "
          f"b={resumo['regressao_coerencia']['b']:.3f} "
          f"({resumo['n_caixas_reais_usadas_na_regressao']} caixas reais)\n")

    print("3) Copiando para o Drive...")
    import shutil
    Path(destino_drive).mkdir(parents=True, exist_ok=True)
    shutil.copy2(destino_csv, Path(destino_drive) / destino_csv.name)
    (Path(destino_drive) / "resumo_tabela_features.json").write_text(
        json.dumps(resumo, indent=2, ensure_ascii=False), encoding="utf-8",
    )
    print(f"\n✅ Tabela salva em {Path(destino_drive) / destino_csv.name}")
    return resumo


if __name__ == "__main__":
    main()

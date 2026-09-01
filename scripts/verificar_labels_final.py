"""
Script de entrada para verificar se labels_final/ ainda bate com o
manifesto congelado -- rode isto antes de qualquer uso importante dos dados
(ex.: antes da Fase 0, antes do Estágio A) para detectar deriva silenciosa.

Uso no Colab:

    from scripts.verificar_labels_final import main
    main(root="/content/drive/MyDrive/PROJETO_MARINHA/Datasets/CITRA-3D-Real",
         splits=["train", "val", "test"])
"""
from __future__ import annotations

import argparse
from pathlib import Path

from src.materialize import verificar_labels_final


def main(root: str, splits: list[str] | None = None) -> bool:
    splits = splits or ["train", "val", "test"]
    root_path = Path(root)
    tudo_ok = True

    for split in splits:
        relatorio = verificar_labels_final(root_path, split)
        if relatorio.ok:
            print(f"✅ {split}: sem deriva detectada.")
        else:
            tudo_ok = False
            print(f"❌ {split}: DERIVA DETECTADA")
            if relatorio.arquivos_alterados:
                print(f"    alterados: {relatorio.arquivos_alterados[:10]}")
            if relatorio.arquivos_faltando:
                print(f"    faltando: {relatorio.arquivos_faltando[:10]}")
            if relatorio.arquivos_novos_nao_registrados:
                print(f"    novos não registrados: {relatorio.arquivos_novos_nao_registrados[:10]}")

    if tudo_ok:
        print("\nTodos os splits batem com o manifesto congelado.")
    else:
        print("\n⚠️  Pelo menos um split não bate com o manifesto. Investigue antes de prosseguir.")

    return tudo_ok


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--splits", nargs="+", default=["train", "val", "test"])
    args = parser.parse_args()
    ok = main(args.root, args.splits)
    raise SystemExit(0 if ok else 1)

"""
Script de entrada para a tarefa -1.4: materializa labels_final/ no
dataset-alvo real (CITRA-3D-Real), com validação e manifesto de hash.

Uso no Colab:

    import sys
    sys.path.insert(0, "/content/synth-detection-attribution")  # ou onde você clonou o repo

    from scripts.materializar_labels_final import main
    main(
        root="/content/drive/MyDrive/PROJETO_MARINHA/Datasets/CITRA-3D-Real",
        labels_subfolder_origem="labels_single_class",
        splits=["train", "val", "test"],
    )

Ou via linha de comando (se o Drive estiver montado como filesystem local):

    python scripts/materializar_labels_final.py \\
        --root /content/drive/MyDrive/PROJETO_MARINHA/Datasets/CITRA-3D-Real \\
        --labels-subfolder-origem labels_single_class \\
        --splits train val test
"""
from __future__ import annotations

import argparse
from pathlib import Path

from src.materialize import materializar_labels_final, InconsistenciaDeDataset


def main(root: str, labels_subfolder_origem: str = "labels_single_class",
          splits: list[str] | None = None) -> None:
    splits = splits or ["train", "val", "test"]
    root_path = Path(root)

    print(f"Materializando labels_final/ a partir de '{labels_subfolder_origem}/'")
    print(f"Raiz: {root_path}")
    print(f"Splits: {splits}\n")

    try:
        relatorios = materializar_labels_final(
            root_dataset_alvo=root_path,
            labels_subfolder_origem=labels_subfolder_origem,
            splits=splits,
        )
    except InconsistenciaDeDataset as e:
        print(f"\n❌ MATERIALIZAÇÃO ABORTADA: {e}")
        print("Nenhum arquivo foi copiado para os splits ainda não processados.")
        raise SystemExit(1)

    print("✅ Materialização concluída:\n")
    for r in relatorios:
        print(f"  {r.split}: {r.n_labels_copiados} labels, {r.n_boxes_total} boxes")
        print(f"    manifesto: {r.caminho_manifesto}")

    total_boxes = sum(r.n_boxes_total for r in relatorios)
    total_imgs = sum(r.n_imagens for r in relatorios)
    print(f"\nTotal: {total_imgs} imagens, {total_boxes} boxes materializados.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, help="raiz do dataset-alvo (contém train/val/test)")
    parser.add_argument("--labels-subfolder-origem", default="labels_single_class")
    parser.add_argument("--splits", nargs="+", default=["train", "val", "test"])
    args = parser.parse_args()
    main(args.root, args.labels_subfolder_origem, args.splits)

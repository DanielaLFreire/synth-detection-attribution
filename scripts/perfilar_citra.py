"""
Script de entrada para a tarefa 0.1: perfila o CITRA-3D-Real com o método
canônico (letterbox), usando labels_final/ já materializado e verificado
(tarefa -1.4).

Uso no Colab:

    import sys
    sys.path.insert(0, "/content/synth-detection-attribution")
    from scripts.perfilar_citra import main

    main(
        root="/content/drive/MyDrive/PROJETO_MARINHA/Datasets/CITRA-3D-Real",
        splits=["train", "val", "test"],
        destino_json="/content/drive/MyDrive/PROJETO_MARINHA/EXPERIMENTO_ATRIBUICAO_CAUSAL/pre_registro/perfil_citra_3d_real.json",
    )
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.profiling import perfilar_dataset


def main(root: str, splits: list[str] | None = None, destino_json: str | None = None) -> dict:
    splits = splits or ["train", "val", "test"]
    root_path = Path(root)

    perfis_por_split = {}
    for split in splits:
        imagens_dir = root_path / split / "images"
        labels_dir = root_path / split / "labels_final"
        if not labels_dir.is_dir():
            raise FileNotFoundError(
                f"{labels_dir} não encontrado -- rode scripts/materializar_labels_final.py "
                "antes desta etapa (tarefa -1.4)."
            )
        print(f"Perfilando {split}...")
        perfis_por_split[split] = perfilar_dataset(imagens_dir, labels_dir)
        d = perfis_por_split[split]["coco_size_distribution"]
        print(f"  {perfis_por_split[split]['n_bboxes_total']} boxes -- "
              f"small={d['small_pct']:.1f}% medium={d['medium_pct']:.1f}% large={d['large_pct']:.1f}%")

    # perfil consolidado (todos os splits juntos) -- útil como referência
    # única do "perfil do alvo" citado nas features relacionais (Família 4)
    total_boxes = sum(p["n_bboxes_total"] for p in perfis_por_split.values())
    total_imgs = sum(p["n_imagens"] for p in perfis_por_split.values())
    print(f"\nTotal consolidado: {total_imgs} imagens, {total_boxes} boxes")

    resultado = {
        "por_split": perfis_por_split,
        "total_boxes_todos_splits": total_boxes,
        "total_imagens_todos_splits": total_imgs,
    }

    if destino_json:
        destino_path = Path(destino_json)
        destino_path.parent.mkdir(parents=True, exist_ok=True)
        destino_path.write_text(json.dumps(resultado, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nResultado salvo em {destino_path}")

    return resultado


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--splits", nargs="+", default=["train", "val", "test"])
    parser.add_argument("--destino-json", default=None)
    args = parser.parse_args()
    main(args.root, args.splits, args.destino_json)

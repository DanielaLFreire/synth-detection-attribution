"""
Fase 3, análise secundária pré-registrada F2 (adendo 2 §4): recall
estratificado por tamanho (small < 32 px vs não-small, referencial
letterbox 640) para os 15 `last.pt`, sobre o split de validação.

Definição fixa (registrada aqui, antes de ver o resultado): predição com
conf >= 0,25 e NMS padrão; um GT conta como detectado se alguma predição
tem IoU >= 0,5 com ele (casamento guloso por confiança, cada predição
usada uma vez). Estrato pelo tamanho do GT a 640.

Uso no Colab (GPU ou CPU -- 332 imagens x 15 modelos, leve):

    import sys
    sys.path.insert(0, "/content/synth-detection-attribution")
    from scripts.recall_por_tamanho_fase3 import main
    main()
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from PIL import Image

from src.compose.compose import ler_caixas_yolo
from src.segmentation.sam_segment import _calcular_iou
from src.factorial import area_letterbox_640

RAIZ = "/content/drive/MyDrive/PROJETO_MARINHA/EXPERIMENTO_ATRIBUICAO_CAUSAL"
RUNS = f"{RAIZ}/fase3/runs"
VAL_IMAGES = "/content/drive/MyDrive/PROJETO_MARINHA/Datasets/CITRA-3D-Real/val/images"
VAL_LABELS = "/content/drive/MyDrive/PROJETO_MARINHA/Datasets/CITRA-3D-Real/val/labels_final"
BRACOS = ["casada__alto", "casada__baixo", "reduzida__alto", "reduzida__baixo", "controle"]
SEEDS = [42, 123, 2024]
CONF, IOU_MIN, LIMIAR_SMALL = 0.25, 0.5, 32 * 32
EXT = (".jpg", ".jpeg", ".png")


def _gts(val_images: Path, val_labels: Path) -> dict[str, list[tuple[tuple, bool]]]:
    """{stem: [((x0,y0,x1,y1), eh_small), ...]}"""
    out = {}
    for label in sorted(val_labels.glob("*.txt")):
        img = next((val_images / f"{label.stem}{e}" for e in EXT if (val_images / f"{label.stem}{e}").exists()), None)
        if img is None:
            continue
        with Image.open(img) as im:
            W, H = im.size
        caixas = []
        for c in ler_caixas_yolo(label, W, H):
            area = float(max(1, c.largura) * max(1, c.altura))
            caixas.append(((c.x0, c.y0, c.x1, c.y1), area_letterbox_640(area, W, H) < LIMIAR_SMALL))
        out[label.stem] = caixas
    return out


def _recall_por_estrato(model, val_images: Path, gts: dict) -> dict:
    det = {"small": [0, 0], "nao_small": [0, 0]}  # [detectados, total]
    for r in model.predict(source=str(val_images), conf=CONF, imgsz=640, stream=True, verbose=False):
        stem = Path(r.path).stem
        if stem not in gts:
            continue
        preds = []
        if r.boxes is not None and len(r.boxes):
            for (x0, y0, x1, y1), cf in zip(r.boxes.xyxy.cpu().numpy(), r.boxes.conf.cpu().numpy()):
                preds.append(((float(x0), float(y0), float(x1), float(y1)), float(cf)))
        preds.sort(key=lambda p: -p[1])
        usados = set()
        for caixa, small in gts[stem]:
            chave = "small" if small else "nao_small"
            det[chave][1] += 1
            for i, (pc, _) in enumerate(preds):
                if i not in usados and _calcular_iou(caixa, pc) >= IOU_MIN:
                    usados.add(i); det[chave][0] += 1; break
    return {k: (v[0] / v[1] if v[1] else float("nan")) for k, v in det.items()} | {"n_small": det["small"][1], "n_nao_small": det["nao_small"][1]}


def main(runs: str = RUNS, val_images: str = VAL_IMAGES, val_labels: str = VAL_LABELS, destino: str = f"{RAIZ}/fase3") -> dict:
    from ultralytics import YOLO
    gts = _gts(Path(val_images), Path(val_labels))
    n_small = sum(s for cs in gts.values() for _, s in cs); n_tot = sum(len(cs) for cs in gts.values())
    print(f"val: {len(gts)} imagens, {n_tot} caixas, {n_small} small ({100*n_small/n_tot:.1f}%)\n")
    linhas = []
    for s in SEEDS:
        for b in BRACOS:
            pesos = Path(runs) / f"{b}_seed{s}" / "weights" / "last.pt"
            r = _recall_por_estrato(YOLO(str(pesos)), Path(val_images), gts)
            linhas.append({"braco": b, "seed": s, **r})
            print(f"  {b:<16} seed {s:<5} recall small={r['small']:.4f}  nao_small={r['nao_small']:.4f}")
    with open(Path(destino) / "recall_por_tamanho_fase3.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0].keys())); w.writeheader(); w.writerows(linhas)
    print(f"\n✅ salvo em {Path(destino) / 'recall_por_tamanho_fase3.csv'}")
    return {"linhas": linhas}


if __name__ == "__main__":
    main()

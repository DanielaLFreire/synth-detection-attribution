"""
Construção do alvo binário do Estágio A (§5.4-5.6 do plano).

Para cada caixa colada (uma linha do manifesto de composição), casa as
detecções da mesma cena (saída de inferir_colagens_sondagem.py) via IoU,
e registra -- por checkpoint/seed -- a MAIOR confiança entre as
detecções que sobrepõem a caixa colada com IoU >= iou_min.

Guardar a confiança máxima (score contínuo) em vez de só "acertou/errou"
é deliberado: o limiar de confiança vira uma decisão posterior e
reversível (feita em CPU sobre esta tabela), e o score contínuo permite
tanto votação majoritária quanto "probabilidade média" entre seeds
(§5.6 do plano), sem voltar à inferência.

Reaproveita `_calcular_iou` de src/segmentation/sam_segment.py -- mesma
função, já testada.
"""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

from src.segmentation.sam_segment import _calcular_iou


def _carregar_deteccoes_por_cena(caminho_csv: Path) -> dict[str, list[tuple[float, float, float, float, float]]]:
    """Lê um CSV de detecções brutas e indexa por cena_stem:
    {cena_stem: [(x0, y0, x1, y1, conf), ...]}."""
    por_cena: dict[str, list] = defaultdict(list)
    with open(caminho_csv, newline="", encoding="utf-8") as f:
        for linha in csv.DictReader(f):
            por_cena[linha["cena_stem"]].append((
                float(linha["x0_px"]), float(linha["y0_px"]),
                float(linha["x1_px"]), float(linha["y1_px"]),
                float(linha["conf"]),
            ))
    return por_cena


def _conf_maxima_com_iou(
    caixa_colada: tuple[float, float, float, float],
    deteccoes: list[tuple[float, float, float, float, float]],
    iou_min: float,
) -> float:
    """Maior confiança entre as detecções que sobrepõem a caixa colada
    com IoU >= iou_min. Retorna 0.0 se nenhuma sobrepõe -- equivale a
    "nenhuma detecção casou", não a "detecção de confiança zero"."""
    melhor = 0.0
    for x0, y0, x1, y1, conf in deteccoes:
        if _calcular_iou(caixa_colada, (x0, y0, x1, y1)) >= iou_min:
            if conf > melhor:
                melhor = conf
    return melhor


def construir_alvo(
    manifesto_csv: Path,
    deteccoes_por_seed: dict[int, Path],
    destino_csv: Path,
    iou_min: float = 0.5,
    conf_min: float = 0.25,
) -> dict:
    """Produz uma tabela com uma linha por caixa colada: todas as colunas
    do manifesto de composição + colunas de alvo:

    - conf_max_seed{S}: maior confiança casada (IoU >= iou_min) por seed.
    - acerto_seed{S}: 1 se conf_max_seed{S} >= conf_min, senão 0.
    - conf_media: média de conf_max entre seeds (score contínuo, §5.6).
    - acerto_votacao: 1 se a maioria das seeds acertou (votação, §5.6).

    Retorna um resumo com as taxas de acerto para inspeção.
    """
    seeds = sorted(deteccoes_por_seed.keys())
    deteccoes = {s: _carregar_deteccoes_por_cena(Path(p)) for s, p in deteccoes_por_seed.items()}

    destino_csv = Path(destino_csv)
    destino_csv.parent.mkdir(parents=True, exist_ok=True)

    n_linhas = 0
    soma_acertos_por_seed = {s: 0 for s in seeds}
    soma_acerto_votacao = 0
    maioria = len(seeds) // 2 + 1

    with open(manifesto_csv, newline="", encoding="utf-8") as f_in, \
         open(destino_csv, "w", newline="", encoding="utf-8") as f_out:
        reader = csv.DictReader(f_in)
        colunas_alvo = (
            [f"conf_max_seed{s}" for s in seeds]
            + [f"acerto_seed{s}" for s in seeds]
            + ["conf_media", "acerto_votacao"]
        )
        writer = csv.DictWriter(f_out, fieldnames=list(reader.fieldnames) + colunas_alvo)
        writer.writeheader()

        for linha in reader:
            cena_stem = Path(linha["imagem_destino_path"]).stem
            caixa = (
                float(linha["caixa_x0_px"]), float(linha["caixa_y0_px"]),
                float(linha["caixa_x1_px"]), float(linha["caixa_y1_px"]),
            )

            confs = {}
            acertos = {}
            for s in seeds:
                conf = _conf_maxima_com_iou(caixa, deteccoes[s].get(cena_stem, []), iou_min)
                confs[s] = conf
                acertos[s] = 1 if conf >= conf_min else 0
                soma_acertos_por_seed[s] += acertos[s]

            acerto_votacao = 1 if sum(acertos.values()) >= maioria else 0
            soma_acerto_votacao += acerto_votacao

            saida = dict(linha)
            for s in seeds:
                saida[f"conf_max_seed{s}"] = f"{confs[s]:.5f}"
                saida[f"acerto_seed{s}"] = acertos[s]
            saida["conf_media"] = f"{sum(confs.values()) / len(seeds):.5f}"
            saida["acerto_votacao"] = acerto_votacao
            writer.writerow(saida)
            n_linhas += 1

    return {
        "n_caixas": n_linhas,
        "iou_min": iou_min,
        "conf_min": conf_min,
        "taxa_acerto_por_seed": {s: soma_acertos_por_seed[s] / n_linhas for s in seeds} if n_linhas else {},
        "taxa_acerto_votacao": soma_acerto_votacao / n_linhas if n_linhas else 0.0,
    }

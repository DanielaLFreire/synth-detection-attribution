"""
Seletor de crop por célula do fatorial 2 × 2 (adendo 2, commit a4ec7ab).

Para cada caixa, decide qual crop colar -- ou deixar a caixa REAL:
- Só caixas PRÉ-REGISTRADAS (`configs/caixas_viaveis_fase3.csv`) recebem
  colagem; qualquer outra fica real, em TODAS as células (adendo 2 §3.1-2).
  Isso garante "mesmas caixas em todas as células" mesmo que uma caixa
  fosse viável só em algumas.
- Entre as permitidas: fonte sorteada uniforme entre as 3 elegíveis
  (1/3 cada em expectativa; proporção real verificada no manifesto),
  crop sorteado uniforme entre os elegíveis da fonte para a célula
  (nível de escala pela área da caixa; nível de contraste fixo da célula).
- Se alguma fonte não tiver `minimo_por_fonte` crops elegíveis para uma
  caixa permitida, é ERRO (a verificação da tarefa 3.2 garante que não
  acontece; se acontecer, o pool mudou -- não silenciar).

Determinismo: o compositor entrega um `random.Random` por caixa, semeado
a partir da seed da célula; o seletor só usa esse rng.
"""
from __future__ import annotations

import bisect
import csv
import random
from dataclasses import dataclass
from pathlib import Path

from src.compose.compose import CaixaAlvo as CaixaCompositor
from .celulas import CropElegivel, FAIXA_CASADA, FONTES_ELEGIVEIS, NIVEIS_CONTRASTE, nivel_contraste


class CaixaPermitidaSemCrop(RuntimeError):
    """Caixa pré-registrada como viável, mas sem crops suficientes nesta
    célula: o pool difere do verificado na tarefa 3.2."""


@dataclass(frozen=True)
class CropIndexado:
    area_px: float
    nome: str
    fonte: str
    caminho: Path


def carregar_caixas_permitidas(caminho_csv: Path) -> set[tuple[str, int]]:
    with open(caminho_csv, newline="", encoding="utf-8") as f:
        return {(l["imagem_id"], int(l["box_index"])) for l in csv.DictReader(f)}


def _faixa_de_areas(area_caixa: float, nivel_escala: str) -> tuple[float, float]:
    """Intervalo [a_min, a_max] de área de crop elegível para a caixa."""
    lo, hi = FAIXA_CASADA
    if nivel_escala == "casada":
        return area_caixa / hi, area_caixa / lo          # [A/2, 2A]
    if nivel_escala == "reduzida":
        return area_caixa / lo, float("inf")             # > 2A (fronteira exclusiva tratada abaixo)
    if nivel_escala == "ampliada":
        return 0.0, area_caixa / hi                      # < A/2
    raise ValueError(nivel_escala)


def construir_seletor_celula(
    pool: list[CropElegivel],
    caminhos_por_nome: dict[str, Path],
    mediana_contraste: float,
    nivel_escala: str,
    nivel_contraste_celula: str,
    caixas_permitidas: set[tuple[str, int]],
    minimo_por_fonte: int = 2,
):
    """Retorna callable (imagem_id, caixa, rng) -> (fonte, caminho) | None."""
    assert nivel_contraste_celula in NIVEIS_CONTRASTE
    indice: dict[str, list[CropIndexado]] = {f: [] for f in FONTES_ELEGIVEIS}
    for c in pool:
        if c.fonte in indice and nivel_contraste(c.contraste, mediana_contraste) == nivel_contraste_celula:
            caminho = caminhos_por_nome.get(c.nome)
            if caminho is not None:
                indice[c.fonte].append(CropIndexado(c.area_px, c.nome, c.fonte, caminho))
    for f in indice:
        indice[f].sort(key=lambda x: x.area_px)
    areas = {f: [x.area_px for x in lst] for f, lst in indice.items()}

    def _elegiveis(fonte: str, area_caixa: float) -> list[CropIndexado]:
        a_min, a_max = _faixa_de_areas(area_caixa, nivel_escala)
        arr = areas[fonte]
        if nivel_escala == "casada":
            i0, i1 = bisect.bisect_left(arr, a_min), bisect.bisect_right(arr, a_max)
        elif nivel_escala == "reduzida":
            i0, i1 = bisect.bisect_right(arr, a_min), len(arr)      # estritamente > 2A
        else:
            i0, i1 = 0, bisect.bisect_left(arr, a_max)              # estritamente < A/2
        return indice[fonte][i0:i1]

    def seletor(imagem_id: str, caixa: CaixaCompositor, rng: random.Random):
        chave = (imagem_id, caixa.box_index)
        if chave not in caixas_permitidas:
            return None  # fica real, em todas as células
        area_caixa = float(max(1, caixa.largura) * max(1, caixa.altura))
        candidatos = {f: _elegiveis(f, area_caixa) for f in FONTES_ELEGIVEIS}
        for f, lst in candidatos.items():
            if len(lst) < minimo_por_fonte:
                raise CaixaPermitidaSemCrop(
                    f"caixa {chave} permitida mas fonte {f} tem {len(lst)} < {minimo_por_fonte} "
                    f"crops elegíveis na célula {nivel_escala}__{nivel_contraste_celula}")
        fonte = rng.choice(FONTES_ELEGIVEIS)
        crop = rng.choice(candidatos[fonte])
        return fonte, crop.caminho

    return seletor

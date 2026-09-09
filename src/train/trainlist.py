"""
Montagem de lista de treino balanceada real/sintético (Fase 1, §9 do plano).

Reescrito do zero neste projeto -- não importa código do projeto anterior
-- mas replica deliberadamente a mesma lógica de balanceamento
(repetir_real × N + sintético × 1 ≈ 50/50), porque aqui a justificativa
original (equilibrar volume num braço de treino supervisionado com GPU)
genuinamente se aplica -- diferente do uso indevido que corrigimos na
tarefa 0.4 (colagens de sondagem do Estágio A, que não treinam nada).

Ver docs/CHANGELOG_metodologico.md para o registro da distinção entre os
dois contextos.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

_EXTENSOES_IMAGEM = (".png", ".jpg", ".jpeg")


@dataclass
class ContagemTrainlist:
    n_real: int          # após repetição
    n_sintetico: int
    n_total: int
    proporcao_real: float


def _listar_imagens(pasta: Path) -> list[Path]:
    return sorted(p for p in Path(pasta).iterdir() if p.suffix.lower() in _EXTENSOES_IMAGEM)


def construir_trainlist_balanceado(
    imagens_reais_dir: Path,
    imagens_sinteticas_dir: Path,
    destino_txt: Path,
    repeat_real: int,
) -> ContagemTrainlist:
    """Escreve um arquivo de texto com um caminho de imagem por linha:
    as imagens reais repetidas `repeat_real` vezes, seguidas das
    sintéticas 1 vez cada. Formato consumido diretamente pelo `train:`
    de um data.yaml do Ultralytics (uma lista de caminhos em vez de uma
    pasta).
    """
    reais = _listar_imagens(imagens_reais_dir)
    sinteticas = _listar_imagens(imagens_sinteticas_dir)

    destino_txt = Path(destino_txt)
    destino_txt.parent.mkdir(parents=True, exist_ok=True)

    with open(destino_txt, "w", encoding="utf-8") as f:
        for _ in range(repeat_real):
            for caminho in reais:
                f.write(str(caminho) + "\n")
        for caminho in sinteticas:
            f.write(str(caminho) + "\n")

    n_real_total = len(reais) * repeat_real
    n_sint_total = len(sinteticas)
    n_total = n_real_total + n_sint_total

    return ContagemTrainlist(
        n_real=n_real_total,
        n_sintetico=n_sint_total,
        n_total=n_total,
        proporcao_real=(n_real_total / n_total) if n_total else 0.0,
    )


def construir_trainlist_real_sobreamostrado(
    imagens_reais_dir: Path,
    destino_txt: Path,
    repeat_real: int,
) -> ContagemTrainlist:
    """Braço de controle (§5.7 do plano): real repetido o MESMO fator do
    braço sintético, com ZERO sintéticos -- isola o efeito da repetição
    do real do efeito da composição em si."""
    reais = _listar_imagens(imagens_reais_dir)
    destino_txt = Path(destino_txt)
    destino_txt.parent.mkdir(parents=True, exist_ok=True)

    with open(destino_txt, "w", encoding="utf-8") as f:
        for _ in range(repeat_real):
            for caminho in reais:
                f.write(str(caminho) + "\n")

    n_real_total = len(reais) * repeat_real
    return ContagemTrainlist(n_real=n_real_total, n_sintetico=0, n_total=n_real_total, proporcao_real=1.0)

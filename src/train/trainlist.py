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


# ---------------------------------------------------------------------------
# Fase 5 (adendo 3, §4.2): trainlist por FRAÇÃO sintética, comprimento fixo
# ---------------------------------------------------------------------------

class TrainlistInvalida(ValueError):
    """A trainlist não tem a composição exigida pelo adendo 3 §4.2."""


def construir_trainlist_fracao(
    imagens_reais: list[Path],
    imagens_sinteticas: list[Path],
    destino_txt: Path,
    repeat_real: int,
) -> ContagemTrainlist:
    """Escreve a trainlist de um braço da Fase 5: cada imagem real
    `repeat_real` vezes (peso IGUAL para todas as reais) e cada sintética
    exatamente 1 vez. Recebe LISTAS explícitas, e não pastas, porque as
    sintéticas da Fase 5 vêm de quatro pastas (uma por célula da Fase 3).

    Levanta TrainlistInvalida se houver caminho duplicado em qualquer das
    listas (duplicata silenciosa daria peso desigual) ou se repeat_real < 1.
    """
    if repeat_real < 1:
        raise TrainlistInvalida("repeat_real deve ser >= 1.")
    reais = [Path(p) for p in imagens_reais]
    sinteticas = [Path(p) for p in imagens_sinteticas]
    if len(set(reais)) != len(reais):
        raise TrainlistInvalida("Lista de reais contém caminhos duplicados.")
    if len(set(sinteticas)) != len(sinteticas):
        raise TrainlistInvalida("Lista de sintéticas contém caminhos duplicados.")
    if set(reais) & set(sinteticas):
        raise TrainlistInvalida("Um mesmo caminho aparece como real e como sintético.")

    destino_txt = Path(destino_txt)
    destino_txt.parent.mkdir(parents=True, exist_ok=True)
    with open(destino_txt, "w", encoding="utf-8") as f:
        for _ in range(repeat_real):
            for caminho in reais:
                f.write(str(caminho) + "\n")
        for caminho in sinteticas:
            f.write(str(caminho) + "\n")

    n_real_total = len(reais) * repeat_real
    n_total = n_real_total + len(sinteticas)
    return ContagemTrainlist(
        n_real=n_real_total,
        n_sintetico=len(sinteticas),
        n_total=n_total,
        proporcao_real=(n_real_total / n_total) if n_total else 0.0,
    )


def verificar_trainlist_fracao(
    destino_txt: Path,
    imagens_reais: list[Path],
    imagens_sinteticas: list[Path],
    repeat_real: int,
    comprimento_esperado: int,
) -> ContagemTrainlist:
    """Relê a trainlist ESCRITA e confere, linha a linha, a composição
    exigida (adendo 3 §8, G1): comprimento exato, cada real exatamente
    `repeat_real` vezes, cada sintética exatamente 1 vez, nenhum caminho
    estranho. Não confia na contagem devolvida pelo construtor."""
    from collections import Counter

    linhas = [l for l in Path(destino_txt).read_text(encoding="utf-8").splitlines() if l.strip()]
    contagem = Counter(linhas)
    reais = {str(Path(p)) for p in imagens_reais}
    sinteticas = {str(Path(p)) for p in imagens_sinteticas}

    if len(linhas) != comprimento_esperado:
        raise TrainlistInvalida(f"Comprimento {len(linhas)} != esperado {comprimento_esperado}.")
    estranhos = set(contagem) - reais - sinteticas
    if estranhos:
        raise TrainlistInvalida(f"{len(estranhos)} caminho(s) fora das listas declaradas, ex.: {sorted(estranhos)[0]}")
    for caminho in reais:
        if contagem.get(caminho, 0) != repeat_real:
            raise TrainlistInvalida(f"Real com peso {contagem.get(caminho, 0)} != {repeat_real}: {caminho}")
    for caminho in sinteticas:
        if contagem.get(caminho, 0) != 1:
            raise TrainlistInvalida(f"Sintética com peso {contagem.get(caminho, 0)} != 1: {caminho}")

    n_real_total = len(reais) * repeat_real
    return ContagemTrainlist(
        n_real=n_real_total,
        n_sintetico=len(sinteticas),
        n_total=len(linhas),
        proporcao_real=n_real_total / len(linhas),
    )

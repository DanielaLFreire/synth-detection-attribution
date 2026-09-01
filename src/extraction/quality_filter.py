"""
Filtro de qualidade de crop unificado (tarefa -1.3 / §8.1 do plano).

Este módulo NÃO decide os valores numéricos dos limiares -- eles chegam
como configuração. Os valores corretos devem ser derivados na tarefa 0.2
(perfis das fontes), a partir da distribuição de tamanho REAL das quatro
fontes deste projeto, não herdados de uma análise feita para uma fonte
específica em outro projeto (ver docs/CHANGELOG_metodologico.md).

O ponto central deste módulo é: o MESMO objeto FiltroConfig deve ser usado
para as quatro fontes, para que "identidade da fonte" nunca se confunda com
"critério de filtro" -- o confound documentado entre ABOShips e InaTechShips
no projeto anterior (MIN_DIM 20px+opacidade vs. 50px sem opacidade).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FiltroConfig:
    """Configuração de filtro, aplicada identicamente a todas as fontes.

    min_dim_px: menor lado do crop (largura ou altura) deve ser >= isso.
    min_cobertura_mascara: fração mínima da bounding box coberta pela
        máscara de segmentação (SAM ou equivalente). None = não exigir
        máscara (aceita crops sem informação de máscara, mas registra isso
        explicitamente no manifesto -- ver `avaliar_crop`).
    exigir_mascara: se True, um crop SEM máscara disponível é
        automaticamente descartado quando min_cobertura_mascara não é None.
        Se False, crops sem máscara passam no filtro de cobertura (mas o
        motivo fica registrado, para auditoria -- não é um "passe" silencioso).
    """
    min_dim_px: int
    min_cobertura_mascara: float | None = None
    exigir_mascara: bool = False


@dataclass
class ResultadoAvaliacao:
    mantido: bool
    motivo: str  # sempre preenchido, mesmo quando mantido=True (ex.: "ok")


def avaliar_crop(
    largura_px: int,
    altura_px: int,
    config: FiltroConfig,
    cobertura_mascara: float | None = None,
) -> ResultadoAvaliacao:
    """Decide se um crop já extraído passa no filtro unificado.

    Esta função não sabe nada sobre a fonte do crop -- é deliberado: o
    mesmo código, com a mesma config, roda para as quatro fontes.
    """
    menor_lado = min(largura_px, altura_px)
    if menor_lado < config.min_dim_px:
        return ResultadoAvaliacao(
            mantido=False,
            motivo=f"dimensao_minima: menor_lado={menor_lado}px < {config.min_dim_px}px",
        )

    if config.min_cobertura_mascara is not None:
        if cobertura_mascara is None:
            if config.exigir_mascara:
                return ResultadoAvaliacao(
                    mantido=False,
                    motivo="sem_mascara_disponivel_e_mascara_e_exigida",
                )
            return ResultadoAvaliacao(
                mantido=True,
                motivo="ok_sem_checagem_de_mascara (mascara indisponivel, exigir_mascara=False)",
            )
        if cobertura_mascara < config.min_cobertura_mascara:
            return ResultadoAvaliacao(
                mantido=False,
                motivo=(
                    f"cobertura_mascara: {cobertura_mascara:.3f} < "
                    f"{config.min_cobertura_mascara:.3f}"
                ),
            )

    return ResultadoAvaliacao(mantido=True, motivo="ok")

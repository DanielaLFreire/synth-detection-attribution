"""
Teste de mediação de `fonte` (P3 pré-registrada, §6 do plano).

Pergunta: a identidade da fonte tem efeito PRÓPRIO sobre o acerto, ou
é só um proxy de propriedades mensuráveis do crop (escala e folga de
anotação) que variam sistematicamente entre fontes?

Desenho:
- Modelo SEM mediadoras: features de crop sem `log_fator_reescala` e sem
  `cobertura_mascara`, + `fonte` (one-hot, 4 colunas). Importância de
  "fonte" = soma das 4 (cluster, §5.5).
- Modelo COM mediadoras: o mesmo + `log_fator_reescala` + `cobertura_mascara`.
- Critério pré-registrado (P3): queda >= 70% na importância de "fonte"
  ao incluir as mediadoras -> "fonte" era proxy. Queda menor -> efeito
  de fonte não capturado pelas features especificadas.

Operacionalização registrada: o plano fala em `folga_anotacao` (fração
de fundo na caixa); `cobertura_mascara` (fração ocupada pelo objeto) é o
seu complemento (folga ≈ 1 - cobertura) e é usada como a mediadora de
folga.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .modelo import criar_modelo, ALVO
from .shap_analise import calcular_shap, ranking_importancia

MEDIADORAS = ["log_fator_reescala", "cobertura_mascara"]
CRITERIO_QUEDA_P3 = 0.70  # pré-registrado em docs/pre_registro/previsoes_fase0.md


def codificar_fonte_one_hot(df: pd.DataFrame, coluna: str = "fonte") -> tuple[pd.DataFrame, list[str]]:
    """Adiciona colunas binárias `fonte_<nome>` (ordem alfabética,
    determinística). Retorna (df, nomes_das_colunas)."""
    saida = df.copy()
    fontes = sorted(saida[coluna].astype(str).unique())
    colunas = []
    for f in fontes:
        nome = f"fonte_{f}"
        saida[nome] = (saida[coluna].astype(str) == f).astype(int)
        colunas.append(nome)
    return saida, colunas


@dataclass
class ResultadoMediacao:
    importancia_fonte_sem_mediadoras: float
    importancia_fonte_com_mediadoras: float
    queda_relativa: float
    criterio: float
    p3_confirmada: bool
    ranking_sem: list[dict]
    ranking_com: list[dict]


def _importancia_cluster(ranking: pd.DataFrame, colunas: list[str]) -> float:
    return float(ranking.loc[ranking["feature"].isin(colunas), "importancia_shap"].sum())


def testar_mediacao_fonte(
    df: pd.DataFrame,
    features_base: list[str],
    mediadoras: list[str] | None = None,
    alvo: str = ALVO,
    seed: int = 42,
    criterio: float = CRITERIO_QUEDA_P3,
) -> ResultadoMediacao:
    """`features_base` NÃO deve conter as mediadoras -- elas são
    adicionadas só no segundo modelo."""
    mediadoras = mediadoras or MEDIADORAS
    assert not set(mediadoras) & set(features_base), "features_base não pode conter as mediadoras"

    df_cod, colunas_fonte = codificar_fonte_one_hot(df)
    y = df_cod[alvo].to_numpy(dtype=int)

    def _ranking(features: list[str]) -> pd.DataFrame:
        X = df_cod[features].to_numpy(dtype=float)
        m = criar_modelo(seed)
        m.fit(X, y)
        return ranking_importancia(calcular_shap(m, X), X, features)

    feats_sem = features_base + colunas_fonte
    feats_com = features_base + mediadoras + colunas_fonte

    rk_sem = _ranking(feats_sem)
    rk_com = _ranking(feats_com)

    imp_sem = _importancia_cluster(rk_sem, colunas_fonte)
    imp_com = _importancia_cluster(rk_com, colunas_fonte)
    queda = (imp_sem - imp_com) / imp_sem if imp_sem > 0 else 0.0

    return ResultadoMediacao(
        importancia_fonte_sem_mediadoras=imp_sem,
        importancia_fonte_com_mediadoras=imp_com,
        queda_relativa=queda,
        criterio=criterio,
        p3_confirmada=queda >= criterio,
        ranking_sem=rk_sem.to_dict(orient="records"),
        ranking_com=rk_com.to_dict(orient="records"),
    )

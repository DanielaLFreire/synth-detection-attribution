"""
Análise controlada por grupo (Estágio A, análise ADICIONAL -- decisão de
2026-09-14, §9 "revisar o alvo do modelo").

Motivação: 57,8% da variância do alvo é entre grupos (geometria herdada
da caixa real, idêntica entre as 20 variações), e o SHAP sobre o alvo
total fica dominado por ela, abafando os 42,2% de variância que vêm do
crop/composição. Aqui, a detectabilidade intrínseca da caixa é controlada
explicitamente, e o modelo responde outra pergunta: DADO que a caixa tem
uma detectabilidade própria, quais propriedades do crop deslocam o
resultado para cima ou para baixo?

Controle: `taxa_grupo_loo` = taxa de acerto das OUTRAS variações do mesmo
grupo (leave-one-out). Nunca inclui o rótulo da própria linha -- caso
contrário o alvo vazaria para dentro de uma feature e o desempenho seria
inflado artificialmente. Testado explicitamente contra vazamento.

Features geométricas puras (area, menor_lado, aspect, pos_v, pos_h) são
REMOVIDAS: são constantes dentro do grupo, e a taxa do grupo as absorve
de forma mais completa. `upsample` removida (redundância exata com o
sinal de log_fator_reescala, importância SHAP = 0 no modelo total).

Esta análise NÃO substitui nem resgata a P1 pré-registrada (refutada
pelo critério original); é reportada separadamente.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .modelo import ALVO, GRUPO

FEATURES_CROP = [
    "log_fator_reescala",
    "distorcao_aspect",
    "crop_menor_lado_original_px",
    "nitidez",
    "contraste",
    "brilho_medio",
    "cobertura_mascara",
]

COVARIAVEL_GRUPO = "taxa_grupo_loo"


def adicionar_taxa_grupo_loo(df: pd.DataFrame, alvo: str = ALVO, grupo: str = GRUPO) -> pd.DataFrame:
    """Adiciona `taxa_grupo_loo`: (soma dos acertos do grupo - acerto da
    própria linha) / (tamanho do grupo - 1). Para grupos de tamanho 1,
    usa a taxa global (não há "outros" para consultar)."""
    saida = df.copy()
    y = saida[alvo].astype(float)
    soma = saida.groupby(grupo)[alvo].transform("sum").astype(float)
    n = saida.groupby(grupo)[alvo].transform("size").astype(float)
    loo = (soma - y) / (n - 1)
    loo = loo.where(n > 1, y.mean())
    saida[COVARIAVEL_GRUPO] = loo
    return saida


def features_controladas() -> list[str]:
    """Features do modelo controlado: covariável de grupo + features de crop."""
    return [COVARIAVEL_GRUPO] + FEATURES_CROP

"""Testes da análise SHAP: ranking, direção, clusters, estabilidade."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("shap", reason="shap não instalado: pip install -r requirements.txt")

from src.attribution.modelo import treinar_modelo_final, FEATURES_PRINCIPAIS
from src.attribution.shap_analise import (
    calcular_shap, ranking_importancia, importancia_por_cluster, estabilidade_bootstrap_por_grupo,
)
from tests.test_modelo import _dataset_sintetico


def test_feature_com_sinal_plantado_fica_em_primeiro():
    """O dado sintético planta sinal em log_fator_reescala (via |lfr|):
    ela deve ser a feature mais importante, sem ambiguidade."""
    df = _dataset_sintetico(n_grupos=300, variacoes=5, seed=3)
    modelo = treinar_modelo_final(df)
    X = df[FEATURES_PRINCIPAIS].to_numpy(dtype=float)
    sv = calcular_shap(modelo, X)
    rk = ranking_importancia(sv, X, FEATURES_PRINCIPAIS)
    assert rk.iloc[0]["feature"] == "log_fator_reescala"
    # a importância da 1a deve ser bem maior que a da 2a
    assert rk.iloc[0]["importancia_shap"] > 2 * rk.iloc[1]["importancia_shap"]


def test_direcao_e_um_coeficiente_em_menos_um_a_um():
    df = _dataset_sintetico(n_grupos=150, seed=4)
    modelo = treinar_modelo_final(df)
    X = df[FEATURES_PRINCIPAIS].to_numpy(dtype=float)
    sv = calcular_shap(modelo, X)
    rk = ranking_importancia(sv, X, FEATURES_PRINCIPAIS)
    assert ((rk["direcao"] >= -1) & (rk["direcao"] <= 1)).all()
    assert list(rk["posicao"]) == list(range(1, len(FEATURES_PRINCIPAIS) + 1))


def test_cluster_soma_importancia_das_features_agrupadas():
    rk = pd.DataFrame({
        "feature": ["a", "b", "c"],
        "importancia_shap": [0.3, 0.2, 0.1],
        "direcao": [0.5, -0.5, 0.1],
        "posicao": [1, 2, 3],
    })
    por_cluster = importancia_por_cluster(rk, clusters={"ab": ["a", "b"]})
    linha_ab = por_cluster[por_cluster["cluster"] == "ab"].iloc[0]
    assert abs(linha_ab["importancia_shap"] - 0.5) < 1e-9
    assert linha_ab["posicao"] == 1
    # feature fora de cluster vira cluster unitário
    assert "c" in set(por_cluster["cluster"])


def test_cluster_padrao_agrupa_tamanho_caixa():
    rk = pd.DataFrame({
        "feature": FEATURES_PRINCIPAIS,
        "importancia_shap": np.linspace(1, 0.1, len(FEATURES_PRINCIPAIS)),
        "direcao": 0.0, "posicao": range(1, len(FEATURES_PRINCIPAIS) + 1),
    })
    por_cluster = importancia_por_cluster(rk)
    clusters = set(por_cluster["cluster"])
    assert "tamanho_caixa" in clusters
    assert "area_caixa_norm" not in clusters
    assert "menor_lado_caixa_px" not in clusters


def test_bootstrap_por_grupo_mantem_feature_com_sinal_no_topo():
    df = _dataset_sintetico(n_grupos=200, variacoes=4, seed=5)
    est = estabilidade_bootstrap_por_grupo(df, n_reamostras=8, k=3, seed=1)
    assert est.n_reamostras == 8
    # a feature com sinal plantado deve ficar no top-3 em (quase) todas as reamostras
    assert est.frequencia_top_k["log_fator_reescala"] >= 0.9
    assert est.posicao_media["log_fator_reescala"] < 2.0


def test_bootstrap_reamostra_grupos_nao_linhas():
    """Sanidade da reamostragem: com grupos de tamanho fixo, o total de
    linhas de cada reamostra é sempre múltiplo do tamanho do grupo."""
    import src.attribution.shap_analise as mod
    df = _dataset_sintetico(n_grupos=20, variacoes=4, seed=6)
    tamanhos = []
    original_concat = pd.concat
    def concat_espiao(partes, **kw):
        out = original_concat(partes, **kw)
        tamanhos.append(len(out))
        return out
    mod.pd.concat = concat_espiao
    try:
        estabilidade_bootstrap_por_grupo(df, n_reamostras=3, k=3, seed=2)
    finally:
        mod.pd.concat = original_concat
    assert all(t % 4 == 0 for t in tamanhos)

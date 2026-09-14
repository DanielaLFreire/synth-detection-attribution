"""Testes da análise controlada por grupo -- em especial, prova de que a
covariável leave-one-out NÃO vaza o rótulo da própria linha."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.attribution.controle_grupo import adicionar_taxa_grupo_loo, features_controladas, FEATURES_CROP, COVARIAVEL_GRUPO
from src.attribution.modelo import validar_por_grupo
from tests.test_modelo import _dataset_sintetico


def test_loo_exclui_o_proprio_rotulo():
    """Grupo com 4 linhas: acertos [1, 1, 0, 0]. Para a 1ª linha (acerto=1),
    a taxa dos OUTROS é (1+0+0)/3 = 1/3 -- não (1+1+0+0)/4 = 0.5."""
    df = pd.DataFrame({
        "grupo_geometrico_id": ["g"] * 4,
        "acerto_votacao": [1, 1, 0, 0],
    })
    out = adicionar_taxa_grupo_loo(df)
    assert out[COVARIAVEL_GRUPO].tolist() == pytest.approx([1/3, 1/3, 2/3, 2/3])


def test_loo_nao_vaza_o_alvo_prova_por_contraste():
    """Prova de não-vazamento: se a covariável fosse a média COM a própria
    linha, um modelo que só a usasse teria desempenho quase perfeito num
    grupo onde a linha é a única diferente. Com LOO, essa linha recebe a
    taxa dos outros (que apontam na direção OPOSTA) -- não há como o
    modelo 'ler' o rótulo dela pela covariável."""
    df = pd.DataFrame({
        "grupo_geometrico_id": ["g"] * 5,
        "acerto_votacao": [1, 0, 0, 0, 0],
    })
    out = adicionar_taxa_grupo_loo(df)
    # a única linha com acerto=1 recebe LOO = 0.0 (todos os outros erraram)
    assert out.loc[0, COVARIAVEL_GRUPO] == 0.0
    # as linhas com acerto=0 recebem LOO = 0.25 (um dos outros acertou)
    assert out.loc[1:, COVARIAVEL_GRUPO].tolist() == pytest.approx([0.25] * 4)
    # ou seja: a covariável é ANTICORRELACIONADA com o rótulo dentro do grupo,
    # o oposto do que aconteceria com vazamento
    assert np.corrcoef(out["acerto_votacao"], out[COVARIAVEL_GRUPO])[0, 1] < 0


def test_grupo_unitario_usa_taxa_global():
    df = pd.DataFrame({
        "grupo_geometrico_id": ["a", "b", "b"],
        "acerto_votacao": [1, 0, 1],
    })
    out = adicionar_taxa_grupo_loo(df)
    assert out.loc[0, COVARIAVEL_GRUPO] == pytest.approx(2/3)  # taxa global
    assert out.loc[1, COVARIAVEL_GRUPO] == 1.0                 # o outro do grupo b acertou
    assert out.loc[2, COVARIAVEL_GRUPO] == 0.0


def test_features_controladas_nao_incluem_geometria_nem_upsample():
    fs = features_controladas()
    assert fs[0] == COVARIAVEL_GRUPO
    for geo in ("area_caixa_norm", "menor_lado_caixa_px", "aspect_caixa", "pos_v", "pos_h", "upsample"):
        assert geo not in fs
    assert set(FEATURES_CROP).issubset(fs)


def test_modelo_controlado_recupera_sinal_de_crop():
    """Dado sintético com sinal em log_fator_reescala + geometria de grupo:
    o modelo controlado deve passar o portão usando só a covariável de
    grupo e as features de crop (sem as geométricas)."""
    df = _dataset_sintetico(n_grupos=250, variacoes=5, seed=7)
    df = adicionar_taxa_grupo_loo(df)
    r = validar_por_grupo(df, features=features_controladas())
    assert r.auc_pr_media > r.taxa_base + 0.05

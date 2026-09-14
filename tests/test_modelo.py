"""Testes do modelo substituto do Estágio A: validação por grupo e portão."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.attribution.modelo import (
    validar_por_grupo, treinar_modelo_final, FEATURES_PRINCIPAIS, PISO_AUC_PR,
)


def _dataset_sintetico(n_grupos=200, variacoes=5, seed=0, sinal_forte=True):
    """Constrói uma tabela onde o alvo depende de log_fator_reescala (se
    sinal_forte) ou é puramente aleatório. Geometria idêntica dentro do
    grupo, como na tabela real."""
    rng = np.random.default_rng(seed)
    linhas = []
    for g in range(n_grupos):
        geo = {
            "area_caixa_norm": rng.uniform(1e-4, 1e-2),
            "menor_lado_caixa_px": rng.uniform(5, 100),
            "pos_v": rng.uniform(0.4, 0.7),
            "pos_h": rng.uniform(0, 1),
            "aspect_caixa": rng.uniform(0.5, 3.0),
        }
        for _ in range(variacoes):
            lfr = rng.normal(0, 1.5)
            feats = {
                **geo,
                "log_fator_reescala": lfr,
                "upsample": int(lfr > 0),
                "distorcao_aspect": rng.normal(0, 0.5),
                "crop_menor_lado_original_px": rng.uniform(5, 400),
                "nitidez": rng.uniform(0, 3000),
                "contraste": rng.uniform(10, 80),
                "brilho_medio": rng.uniform(50, 200),
                "cobertura_mascara": rng.uniform(0.2, 1.0),
            }
            if sinal_forte:
                # acerto mais provável quando |log_fator_reescala| é pequeno (escala casada)
                p = 1 / (1 + np.exp(2.0 * abs(lfr) - 3.5))  # taxa base ~0,69, como a real (0,70)
            else:
                p = 0.7
            feats["acerto_votacao"] = int(rng.random() < p)
            feats["grupo_geometrico_id"] = f"g{g}"
            linhas.append(feats)
    return pd.DataFrame(linhas)


def test_validacao_por_grupo_retorna_um_valor_por_fold():
    df = _dataset_sintetico()
    r = validar_por_grupo(df, n_folds=5)
    assert r.n_folds == 5
    assert len(r.auc_pr_por_fold) == 5
    assert len(r.auc_roc_por_fold) == 5
    assert 0.0 <= r.auc_pr_media <= 1.0


def test_sinal_forte_passa_o_portao():
    df = _dataset_sintetico(sinal_forte=True)
    r = validar_por_grupo(df)
    assert r.passou_portao, f"AUC-PR média {r.auc_pr_media:.3f} abaixo do piso {r.piso}"


def test_alvo_aleatorio_nao_passa_o_portao():
    """Alvo sem relação com as features -> AUC-PR perto da taxa base
    (~0,70), abaixo do piso 0,78. Confirma que o portão rejeita ruído."""
    df = _dataset_sintetico(sinal_forte=False, seed=1)
    r = validar_por_grupo(df)
    assert not r.passou_portao
    assert abs(r.auc_pr_media - r.taxa_base) < 0.08


def test_piso_pre_registrado_e_0_78():
    assert PISO_AUC_PR == 0.78


def test_grupos_nao_vazam_entre_folds():
    """Cada grupo deve aparecer em exatamente um fold de teste."""
    from sklearn.model_selection import GroupKFold
    df = _dataset_sintetico(n_grupos=50, variacoes=4)
    grupos = df["grupo_geometrico_id"].to_numpy()
    vistos = set()
    for _, teste_idx in GroupKFold(n_splits=5).split(df, groups=grupos):
        grupos_teste = set(grupos[teste_idx])
        assert not (grupos_teste & vistos), "grupo apareceu em mais de um fold de teste"
        vistos |= grupos_teste
    assert vistos == set(grupos)


def test_modelo_final_treina_e_prediz():
    df = _dataset_sintetico()
    modelo = treinar_modelo_final(df)
    prob = modelo.predict_proba(df[FEATURES_PRINCIPAIS].to_numpy(dtype=float))[:, 1]
    assert prob.shape[0] == len(df)
    assert ((prob >= 0) & (prob <= 1)).all()

"""Testes do teste de mediação de fonte (P3)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("shap", reason="shap não instalado: pip install -r requirements.txt")

from src.attribution import mediacao as med
from src.attribution.mediacao import codificar_fonte_one_hot, CRITERIO_QUEDA_P3
testar_mediacao_fonte = med.testar_mediacao_fonte
testar_mediacao_fonte.__test__ = False  # não é um teste, é a função sob teste


def test_one_hot_determinístico_e_exclusivo():
    df = pd.DataFrame({"fonte": ["B", "A", "B", "C"]})
    out, cols = codificar_fonte_one_hot(df)
    assert cols == ["fonte_A", "fonte_B", "fonte_C"]  # ordem alfabética
    assert out[cols].sum(axis=1).tolist() == [1, 1, 1, 1]  # exatamente uma fonte por linha
    assert out["fonte_B"].tolist() == [1, 0, 1, 0]


def test_criterio_pre_registrado_e_70_por_cento():
    assert CRITERIO_QUEDA_P3 == 0.70


def _dados_com_fonte_proxy(n=3000, seed=0, fonte_proxy=True):
    """Dois cenários:
    - fonte_proxy=True: a fonte determina a ESCALA, e a escala determina o
      acerto. A fonte não tem efeito próprio -> mediação total.
    - fonte_proxy=False: a fonte tem efeito PRÓPRIO, independente da escala."""
    rng = np.random.default_rng(seed)
    fonte = rng.choice(["X", "Y"], size=n)
    if fonte_proxy:
        # fonte X -> escala casada (log ~ 0); fonte Y -> ampliada demais (log ~ 3)
        lfr = np.where(fonte == "X", rng.normal(0, 0.3, n), rng.normal(3, 0.3, n))
        p = 1 / (1 + np.exp(1.5 * np.abs(lfr) - 2.5))
    else:
        lfr = rng.normal(0, 1, n)  # escala independente da fonte
        p = np.where(fonte == "X", 0.85, 0.45)  # efeito próprio da fonte
    return pd.DataFrame({
        "fonte": fonte,
        "log_fator_reescala": lfr,
        "cobertura_mascara": rng.uniform(0.3, 0.9, n),
        "contraste": rng.uniform(10, 80, n),
        "nitidez": rng.uniform(0, 2000, n),
        "acerto_votacao": (rng.random(n) < p).astype(int),
    })


def test_mediacao_total_quando_fonte_e_proxy_de_escala():
    df = _dados_com_fonte_proxy(fonte_proxy=True)
    r = testar_mediacao_fonte(df, features_base=["contraste", "nitidez"])
    assert r.importancia_fonte_sem_mediadoras > 0.1  # sem a escala, fonte parece importar
    assert r.queda_relativa >= 0.7, f"queda {r.queda_relativa:.2f} < 0.7"
    assert r.p3_confirmada


def test_sem_mediacao_quando_fonte_tem_efeito_proprio():
    df = _dados_com_fonte_proxy(fonte_proxy=False, seed=1)
    r = testar_mediacao_fonte(df, features_base=["contraste", "nitidez"])
    assert r.importancia_fonte_sem_mediadoras > 0.1
    assert r.queda_relativa < 0.5, f"queda {r.queda_relativa:.2f} deveria ser pequena"
    assert not r.p3_confirmada


def test_recusa_features_base_com_mediadora():
    df = _dados_com_fonte_proxy(n=200)
    with pytest.raises(AssertionError):
        testar_mediacao_fonte(df, features_base=["contraste", "log_fator_reescala"])

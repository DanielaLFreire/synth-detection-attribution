"""Testes da análise fatorial 2x2 (adendo 2 §4, §6)."""
from __future__ import annotations

import math
import numpy as np
import pytest

from src.factorial.analise import (
    contraste, holm, anova_2x2_bloco, analisar_fatorial, _sf_t, _sf_f, _betainc_reg, PISO_PP,
)


def test_piso_e_2pp():
    assert PISO_PP == 2.0


def test_beta_incompleta_valores_conhecidos():
    assert _betainc_reg(1, 1, 0.3) == pytest.approx(0.3, abs=1e-9)       # I_x(1,1) = x
    assert _betainc_reg(2, 3, 0.5) == pytest.approx(0.6875, abs=1e-9)    # 1 - (1-x)^4 (1+4x) para a=2,b=3? -> checa numérico
    assert _betainc_reg(0.5, 0.5, 0.5) == pytest.approx(0.5, abs=1e-9)


def test_cauda_t_valores_tabelados():
    # t=2.920, df=2 -> p unilateral 0.05 ; t=4.303, df=2 -> 0.025
    assert _sf_t(2.920, 2) == pytest.approx(0.05, abs=2e-3)
    assert _sf_t(4.303, 2) == pytest.approx(0.025, abs=2e-3)
    assert _sf_t(0.0, 5) == pytest.approx(0.5)


def test_cauda_f_valores_tabelados():
    # F(1,6) crítico 5% = 5.987 ; F(2,6) = 5.143
    assert _sf_f(5.987, 1, 6) == pytest.approx(0.05, abs=2e-3)
    assert _sf_f(5.143, 2, 6) == pytest.approx(0.05, abs=2e-3)


def test_contraste_real_exige_piso_e_sinal_em_todas():
    c = contraste("x", {42: 0.03, 123: 0.025, 2024: 0.035})   # +3.0 pp, todas positivas
    assert c.veredito == "real" and c.media_pp == pytest.approx(3.0)
    c2 = contraste("x", {42: 0.03, 123: 0.05, 2024: -0.005})  # média 2.5 pp mas uma seed negativa
    assert c2.veredito == "direcao"
    c3 = contraste("x", {42: 0.01, 123: 0.008, 2024: 0.012})  # sinal consistente, 1.0 pp
    assert c3.veredito == "direcao"
    c4 = contraste("x", {42: 0.01, 123: -0.01, 2024: 0.0})    # sem consistência
    assert c4.veredito == "ruido"


def test_contraste_d_cohen_e_leave_one_out():
    c = contraste("x", {42: 0.02, 123: 0.02, 2024: 0.02})
    assert math.isinf(c.d_cohen)  # desvio zero, média não nula
    c = contraste("x", {42: 0.01, 123: 0.02, 2024: 0.03})
    assert c.d_cohen == pytest.approx(2.0 / 1.0)
    assert c.leave_one_seed_out_pp[42] == pytest.approx(2.5)
    assert c.leave_one_seed_out_pp[2024] == pytest.approx(1.5)


def test_holm_ajusta_e_mantem_monotonicidade():
    a = contraste("a", {1: 0.03, 2: 0.031, 3: 0.029})   # p muito pequeno
    b = contraste("b", {1: 0.01, 2: -0.01, 3: 0.0})     # p ~ 1
    holm([a, b])
    assert a.p_holm == pytest.approx(min(1.0, 2 * a.p))
    assert b.p_holm == 1.0
    assert a.p_holm <= b.p_holm


def test_anova_recupera_efeito_plantado():
    """Efeito de escala de +4 pp puro, sem contraste nem interação, sem
    efeito de seed: SS_escala = N * (2 pp)^2, demais ~0."""
    seeds = [1, 2, 3]
    rec = {"casada__alto": {s: 0.72 for s in seeds}, "casada__baixo": {s: 0.72 for s in seeds},
           "reduzida__alto": {s: 0.68 for s in seeds}, "reduzida__baixo": {s: 0.68 for s in seeds}}
    a = anova_2x2_bloco(rec)
    assert a.ss["escala"] == pytest.approx(12 * 0.02 ** 2, abs=1e-12)
    assert a.ss["contraste"] == pytest.approx(0.0, abs=1e-12)
    assert a.ss["interacao"] == pytest.approx(0.0, abs=1e-12)
    assert a.ss["seed"] == pytest.approx(0.0, abs=1e-12)
    assert a.df == {"escala": 1, "contraste": 1, "interacao": 1, "seed": 2, "erro": 6}


def test_anova_soma_de_quadrados_fecha():
    rng = np.random.default_rng(0)
    seeds = [1, 2, 3]
    rec = {b: {s: float(rng.uniform(0.6, 0.75)) for s in seeds}
           for b in ("casada__alto", "casada__baixo", "reduzida__alto", "reduzida__baixo")}
    a = anova_2x2_bloco(rec)
    Y = np.array([[rec[b][s] for s in seeds] for b in rec])
    assert sum(a.ss.values()) == pytest.approx(float(((Y - Y.mean()) ** 2).sum()), abs=1e-12)


def test_analisar_fatorial_estrutura():
    seeds = [1, 2, 3]
    rec = {b: {s: 0.7 + 0.001 * i for s in seeds} for i, b in enumerate(
        ("casada__alto", "casada__baixo", "reduzida__alto", "reduzida__baixo", "controle"))}
    out = analisar_fatorial(rec)
    assert set(out["F1"]) == {"P5b", "P8"}
    assert set(out["F3"]["P10_por_celula"]) == {"casada__alto", "casada__baixo", "reduzida__alto", "reduzida__baixo"}
    assert out["F1"]["P5b"].p_holm is not None

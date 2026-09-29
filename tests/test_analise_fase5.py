"""Fase 5: análise pré-registrada (adendo 3 §5–§7), testada em dados
fictícios ANTES de qualquer métrica real ser aberta."""
from __future__ import annotations

import json
import math

import numpy as np
import pytest

from src.factorial.analise_fase5 import (
    BRACOS, ORCAMENTOS, SEEDS, anova_2x3_bloco, analisar, auc_normalizada, contraste_f5,
    holm, metricas_de_results, t_quantil, tabela_markdown, _tost_p,
)


# --- distribuição t ---

@pytest.mark.parametrize("prob,df,tabelado", [(0.975, 4, 2.776445), (0.95, 4, 2.131847), (0.975, 2, 4.302653), (0.975, 30, 2.042272)])
def test_quantis_t_contra_tabela(prob, df, tabelado):
    assert t_quantil(prob, df) == pytest.approx(tabelado, abs=1e-5)


# --- regra de decisão §6.1 ---

def _d(vals_pp):
    return {s: v / 100 for s, v in zip(SEEDS, vals_pp)}


def test_ic_calculado_a_mao():
    c = contraste_f5("x", "F1", _d([-1.0, -2.0, -1.5, -0.5, -2.5]))
    media, dp = -1.5, np.std([-1.0, -2.0, -1.5, -0.5, -2.5], ddof=1)
    meia = 2.776445 * dp / math.sqrt(5)
    assert c.media_pp == pytest.approx(media)
    assert c.ic95_pp == pytest.approx((media - meia, media + meia), abs=1e-5)


def test_pior():
    assert contraste_f5("x", "F1", _d([-2.0, -1.8, -2.2, -1.9, -2.1])).veredito == "sintetico_pior"


def test_melhor():
    assert contraste_f5("x", "F1", _d([2.0, 1.8, 2.2, 1.9, 2.1])).veredito == "sintetico_melhor"


def test_equivalente():
    c = contraste_f5("x", "F1", _d([0.1, -0.2, 0.15, -0.05, 0.0]))
    assert c.veredito == "equivalente" and c.p_tost < 0.05


def test_inconclusivo():
    c = contraste_f5("x", "F1", _d([2.0, -1.5, 1.0, -2.0, 0.8]))
    assert c.veredito == "inconclusivo" and c.subdimensionado


def test_diferenca_detectavel_mas_dentro_da_margem():
    c = contraste_f5("x", "F1", _d([-0.30, -0.35, -0.25, -0.32, -0.28]))
    assert c.veredito == "sintetico_pior" and c.tambem_dentro_da_margem


def test_tost_equivale_a_ic90_dentro_da_margem():
    rng = np.random.default_rng(0)
    for _ in range(300):
        vals = rng.normal(rng.uniform(-1.5, 1.5), rng.uniform(0.05, 1.2), 5)
        c = contraste_f5("x", "F1", _d(list(vals)))
        dentro = c.ic90_pp[0] > -1 and c.ic90_pp[1] < 1
        assert (c.p_tost < 0.05) == dentro


def test_interacao():
    assert contraste_f5("x", "F1", _d([1.0, 1.2, 0.9, 1.1, 1.0]), tipo="interacao").veredito == "interacao_positiva"
    assert contraste_f5("x", "F1", _d([1.0, -1.2, 0.9, -1.1, 0.3]), tipo="interacao").veredito == "interacao_nao_detectada"


def test_subdimensionado_so_acima_de_0_8():
    assert not contraste_f5("x", "F1", _d([0.0, 0.5, -0.5, 0.3, -0.3])).subdimensionado
    assert contraste_f5("x", "F1", _d([0.0, 1.5, -1.5, 1.0, -1.0])).subdimensionado


def test_holm():
    cs = [contraste_f5(n, "F1", _d(v)) for n, v in
          (("a", [-2, -1.9, -2.1, -2, -2.05]), ("b", [0.1, -0.2, 0.3, 0, -0.1]), ("c", [1, 0.2, 0.8, 0.5, 0.9]))]
    ps = sorted(c.p for c in cs)
    holm(cs)
    hs = sorted(c.p_holm for c in cs)
    assert hs[0] == pytest.approx(min(1, 3 * ps[0]))
    assert hs == sorted(hs) and all(h >= p for h, p in zip(hs, ps))


# --- ANOVA 2×3 com bloco ---

def _tabela(efeito_fracao=None, efeito_orc=None, interacao=None, ruido=0.0, seed=1, base=0.70):
    rng = np.random.default_rng(seed)
    ef = efeito_fracao or {"C": 0, "M25": 0, "M50": 0}
    eo = efeito_orc or {"S1": 0, "S2": 0}
    it = interacao or {}
    bloco = dict(zip(SEEDS, [0.004, -0.003, 0.001, -0.002, 0.0]))
    return {o: {b: {s: base + ef[b] + eo[o] + it.get((o, b), 0) + bloco[s] + rng.normal(0, ruido) for s in SEEDS}
                for b in BRACOS} for o in ORCAMENTOS}


def test_anova_particao_e_graus_de_liberdade():
    a = anova_2x3_bloco(_tabela({"C": 0, "M25": 0.01, "M50": 0.02}, {"S1": -0.01, "S2": 0.01}, ruido=0.003))
    assert a.df == {"orcamento": 1, "fracao": 2, "interacao": 2, "seed": 4, "erro": 20}
    soma = sum(a.ss[k] for k in ("orcamento", "fracao", "interacao", "seed", "erro"))
    assert soma == pytest.approx(a.ss["total"])
    assert a.p["fracao"] < 0.001 and a.p["orcamento"] < 0.001


def test_anova_aditiva_sem_interacao():
    a = anova_2x3_bloco(_tabela({"C": 0, "M25": 0.01, "M50": 0.02}, {"S1": 0, "S2": 0.01}, ruido=0.0))
    assert a.ss["interacao"] == pytest.approx(0, abs=1e-9)


# --- métricas de results.csv ---

def test_auc_constante_e_linear():
    ep = list(range(1, 31))
    assert auc_normalizada(ep, [0.7] * 30) == pytest.approx(0.7)
    assert auc_normalizada(ep, [e / 30 for e in ep]) == pytest.approx((1 / 30 + 1) / 2)


def test_metricas_de_results(tmp_path):
    p = tmp_path / "results.csv"
    linhas = ["  epoch, time, metrics/recall(B), metrics/mAP50(B)"]
    rec = [0.5, 0.7, 0.72, 0.72, 0.69]
    for i, r in enumerate(rec, 1):
        linhas.append(f"{i},1,{r},{r + 0.05}")
    p.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    m = metricas_de_results(p, 5)
    assert m.recall == 0.69 and m.map50 == pytest.approx(0.74)
    assert m.epoca_pico == 3 and m.passo_pico == 3 * 337  # empate: primeira ocorrência
    with pytest.raises(ValueError):
        metricas_de_results(p, 6)


# --- análise completa ---

def _todas(recall):
    return dict(recall=recall, map50=recall, auc=recall, small=recall)


def test_p12_e_metade_de_p11_com_mesmo_p():
    r = analisar(**_todas(_tabela({"C": 0, "M25": 0.005, "M50": -0.02}, ruido=0.003)))
    p11, p12, p13 = r["F1"]
    for s in SEEDS:
        assert p12["por_seed_pp"][s] == pytest.approx(p11["por_seed_pp"][s] / 2)
    assert p12["p"] == pytest.approx(p11["p"]) and "P11/2" in p12["nota"]


def test_cenario_sintetico_pior_em_s2():
    r = analisar(**_todas(_tabela({"C": 0, "M25": -0.015, "M50": -0.03}, ruido=0.002)))
    assert r["F1"][0]["veredito"] == "sintetico_pior"
    assert all(c["p_holm"] is not None for c in r["F1"])


def test_cenario_regularizacao_interacao_positiva():
    """Sintético neutro em S1 e +2 pp em S2 -> P11 melhor, P13 interação positiva."""
    t = _tabela(interacao={("S2", "M50"): 0.02, ("S2", "M25"): 0.01}, ruido=0.002)
    r = analisar(**_todas(t))
    assert r["F1"][0]["veredito"] == "sintetico_melhor"
    assert r["F1"][2]["veredito"] == "interacao_positiva"


def test_cenario_nulo_equivalente():
    r = analisar(**_todas(_tabela(ruido=0.001)))
    assert r["F1"][0]["veredito"] == "equivalente"


def test_familias_e_saida_serializavel():
    r = analisar(**_todas(_tabela(ruido=0.003)), pico={o: {b: {s: 1000 for s in SEEDS} for b in BRACOS} for o in ORCAMENTOS})
    assert len(r["F1"]) == 3 and len(r["F2"]) == 4 and len(r["F3"]) == 4
    assert all(c["familia"] == "F2" and c["p_holm"] is not None for c in r["F2"])
    assert all(c["veredito"] == "descritivo" for c in r["F3"])
    json.dumps(r)
    md = tabela_markdown(r)
    assert "P11" in md and "F2a" in md and "F3c" in md


# --- trava de execução única ---

def test_analise_recusa_segunda_execucao(tmp_path):
    from scripts.analisar_fase5 import AnaliseJaExecutada, verificar_pronto
    (tmp_path / "analise_val_executada.json").write_text("{}", encoding="utf-8")
    with pytest.raises(AnaliseJaExecutada):
        verificar_pronto(str(tmp_path))


def test_analise_recusa_sem_30_execucoes(tmp_path):
    from scripts.analisar_fase5 import verificar_pronto
    (tmp_path / "portao_g2.json").write_text(json.dumps({"veredito": "GO"}), encoding="utf-8")
    with pytest.raises(RuntimeError, match="não concluída"):
        verificar_pronto(str(tmp_path))


def test_tost_com_media_fora_da_margem_nao_rejeita():
    """Regressão: _sf_t da Fase 3 só vale para t >= 0; o TOST precisa da
    cauda correta para t negativo."""
    c = contraste_f5("x", "F1", _d([1.24, 1.35, 1.30, 1.28, 1.33]))
    assert c.p_tost > 0.5 and c.veredito == "sintetico_melhor"

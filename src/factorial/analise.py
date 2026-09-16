"""
Análise do fatorial 2 × 2 da Fase 3 (adendo 2, commit a4ec7ab, §4 e §6).

Entrada: recall na época 150 por (braço, seed), com braços
{casada__alto, casada__baixo, reduzida__alto, reduzida__baixo, controle}.

Saídas:
- ANOVA 2 × 2 com seed como BLOCO (somas de quadrados clássicas; df:
  escala 1, contraste 1, interação 1, seed n_seeds-1, erro o resto).
- Contrastes pré-registrados calculados POR SEED e depois agregados:
  P5b' (casada − reduzida), P8 (alto − baixo), P9 (interação),
  P10 (cada célula − controle). t pareado por seed, d de Cohen pareado
  (média / desvio das diferenças), leave-one-seed-out.
- Regra de leitura do adendo (§4): efeito "real" se |média| > piso E mesmo
  sinal em TODAS as seeds; "direção" se sinal consistente em >= 2/3 mas
  |média| <= piso; senão "indistinguível de ruído".
- Holm–Bonferroni dentro da família F1 (P5b', P8).

Tudo em pontos percentuais (pp) nas saídas de contraste.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

BRACOS_CELULA = ["casada__alto", "casada__baixo", "reduzida__alto", "reduzida__baixo"]
CONTROLE = "controle"
PISO_PP = 2.0  # Fase 1, banda 1, maior amplitude entre braços


def _t_pareado(diferencas: np.ndarray) -> tuple[float, float]:
    """t e p bilateral para média das diferenças = 0 (df = n-1)."""
    n = len(diferencas)
    if n < 2:
        return float("nan"), float("nan")
    sd = diferencas.std(ddof=1)
    if sd == 0:
        return float("inf") if diferencas.mean() != 0 else 0.0, 0.0 if diferencas.mean() != 0 else 1.0
    t = diferencas.mean() / (sd / math.sqrt(n))
    p = 2.0 * _sf_t(abs(t), n - 1)
    return float(t), float(p)


def _sf_t(t: float, df: int) -> float:
    """Cauda superior da t de Student via beta incompleta regularizada
    (sem scipy). P(T > t)."""
    x = df / (df + t * t)
    return 0.5 * _betainc_reg(df / 2.0, 0.5, x)


def _betainc_reg(a: float, b: float, x: float) -> float:
    """I_x(a, b) por fração continuada (Numerical Recipes, betacf)."""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    lbeta = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
    front = math.exp(lbeta + a * math.log(x) + b * math.log(1 - x))
    if x < (a + 1) / (a + b + 2):
        return front * _betacf(a, b, x) / a
    return 1.0 - front * _betacf(b, a, 1 - x) / b


def _betacf(a: float, b: float, x: float, max_iter: int = 300, eps: float = 1e-14) -> float:
    qab, qap, qam = a + b, a + 1, a - 1
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) > 1e-300 else 1e-300)
    h = d
    for m in range(1, max_iter + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d; d = 1.0 / (d if abs(d) > 1e-300 else 1e-300)
        c = 1.0 + aa / (c if abs(c) > 1e-300 else 1e-300)
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d; d = 1.0 / (d if abs(d) > 1e-300 else 1e-300)
        c = 1.0 + aa / (c if abs(c) > 1e-300 else 1e-300)
        dl = d * c
        h *= dl
        if abs(dl - 1.0) < eps:
            break
    return h


def _sf_f(f: float, df1: int, df2: int) -> float:
    """P(F > f)."""
    if f <= 0:
        return 1.0
    x = df2 / (df2 + df1 * f)
    return _betainc_reg(df2 / 2.0, df1 / 2.0, x)


@dataclass
class Contraste:
    nome: str
    por_seed_pp: dict[int, float]
    media_pp: float
    dp_pp: float
    d_cohen: float
    t: float
    p: float
    sinal_consistente_todas: bool
    n_seeds_mesmo_sinal_da_media: int
    veredito: str
    leave_one_seed_out_pp: dict[int, float] = field(default_factory=dict)
    p_holm: float | None = None


def _veredito(media_pp: float, sinais_iguais_todas: bool, n_mesmo_sinal: int, n_seeds: int, piso: float) -> str:
    if abs(media_pp) > piso and sinais_iguais_todas:
        return "real"
    if n_mesmo_sinal >= math.ceil(2 * n_seeds / 3):
        return "direcao"
    return "ruido"


def contraste(nome: str, diffs_por_seed: dict[int, float], piso: float = PISO_PP) -> Contraste:
    seeds = sorted(diffs_por_seed)
    d = np.array([diffs_por_seed[s] for s in seeds], dtype=float) * 100.0  # pp
    media = float(d.mean())
    dp = float(d.std(ddof=1)) if len(d) > 1 else 0.0
    d_cohen = media / dp if dp > 0 else (float("inf") if media != 0 else 0.0)
    t, p = _t_pareado(d)
    sinais = np.sign(d)
    todas = bool(len(set(sinais)) == 1 and sinais[0] != 0)
    n_mesmo = int(np.sum(sinais == np.sign(media))) if media != 0 else 0
    loo = {s: float(np.mean([diffs_por_seed[o] * 100 for o in seeds if o != s])) for s in seeds} if len(seeds) > 2 else {}
    return Contraste(
        nome=nome, por_seed_pp={s: float(v) for s, v in zip(seeds, d)}, media_pp=media, dp_pp=dp,
        d_cohen=float(d_cohen), t=t, p=p, sinal_consistente_todas=todas,
        n_seeds_mesmo_sinal_da_media=n_mesmo,
        veredito=_veredito(media, todas, n_mesmo, len(seeds), piso), leave_one_seed_out_pp=loo,
    )


def holm(contrastes: list[Contraste]) -> None:
    """Holm–Bonferroni in-place sobre `p` -> `p_holm` (uma família)."""
    validos = [c for c in contrastes if not math.isnan(c.p)]
    ordem = sorted(validos, key=lambda c: c.p)
    m = len(ordem)
    anterior = 0.0
    for i, c in enumerate(ordem):
        ajust = min(1.0, (m - i) * c.p)
        anterior = max(anterior, ajust)  # monotonicidade
        c.p_holm = anterior


@dataclass
class ANOVA2x2Bloco:
    ss: dict[str, float]
    df: dict[str, int]
    ms: dict[str, float]
    f: dict[str, float]
    p: dict[str, float]


def anova_2x2_bloco(recall: dict[str, dict[int, float]]) -> ANOVA2x2Bloco:
    """recall[braço][seed], para os 4 braços de célula. Blocos = seeds."""
    seeds = sorted(next(iter(recall.values())))
    Y = np.array([[recall[b][s] for s in seeds] for b in BRACOS_CELULA])  # 4 x n_seeds
    n_s = len(seeds)
    escala = np.array([1, 1, -1, -1])      # casada=+1, reduzida=-1
    contr = np.array([1, -1, 1, -1])       # alto=+1, baixo=-1
    inter = escala * contr
    media = Y.mean()
    ss_total = float(((Y - media) ** 2).sum())
    # efeitos fatoriais (design balanceado): SS = (soma ponderada)^2 / N
    N = Y.size
    def ss_efeito(vetor):
        tot = float((vetor[:, None] * Y).sum())
        return tot * tot / N
    ss = {"escala": ss_efeito(escala), "contraste": ss_efeito(contr), "interacao": ss_efeito(inter)}
    medias_seed = Y.mean(axis=0)
    ss["seed"] = float(4 * ((medias_seed - media) ** 2).sum())
    ss["erro"] = ss_total - sum(ss.values())
    df = {"escala": 1, "contraste": 1, "interacao": 1, "seed": n_s - 1}
    df["erro"] = N - 1 - sum(df.values())
    ms = {k: ss[k] / df[k] if df[k] > 0 else float("nan") for k in ss}
    f = {k: (ms[k] / ms["erro"] if ms["erro"] > 0 else float("inf")) for k in ("escala", "contraste", "interacao", "seed")}
    p = {k: _sf_f(f[k], df[k], df["erro"]) if df["erro"] > 0 else float("nan") for k in f}
    return ANOVA2x2Bloco(ss=ss, df=df, ms=ms, f=f, p=p)


def analisar_fatorial(recall: dict[str, dict[int, float]], piso: float = PISO_PP) -> dict:
    """Análise completa. `recall[braço][seed]` inclui os 4 braços e o controle."""
    seeds = sorted(recall[CONTROLE])
    r = recall
    def por_seed(fn):
        return {s: fn(s) for s in seeds}
    c_escala = contraste("P5b'_casada_menos_reduzida", por_seed(
        lambda s: (r["casada__alto"][s] + r["casada__baixo"][s]) / 2 - (r["reduzida__alto"][s] + r["reduzida__baixo"][s]) / 2), piso)
    c_contr = contraste("P8_alto_menos_baixo", por_seed(
        lambda s: (r["casada__alto"][s] + r["reduzida__alto"][s]) / 2 - (r["casada__baixo"][s] + r["reduzida__baixo"][s]) / 2), piso)
    c_inter = contraste("P9_interacao", por_seed(
        lambda s: (r["casada__alto"][s] - r["casada__baixo"][s]) - (r["reduzida__alto"][s] - r["reduzida__baixo"][s])), piso)
    c_ctrl = {b: contraste(f"P10_{b}_menos_controle", por_seed(lambda s, b=b: r[b][s] - r[CONTROLE][s]), piso) for b in BRACOS_CELULA}
    c_media_cel = contraste("P10_media_celulas_menos_controle", por_seed(
        lambda s: float(np.mean([r[b][s] for b in BRACOS_CELULA])) - r[CONTROLE][s]), piso)
    holm([c_escala, c_contr])  # família F1
    return {
        "piso_pp": piso, "seeds": seeds,
        "anova_2x2_bloco_seed": anova_2x2_bloco({b: r[b] for b in BRACOS_CELULA}),
        "F1": {"P5b": c_escala, "P8": c_contr},
        "F3": {"P9": c_inter, "P10_por_celula": c_ctrl, "P10_media": c_media_cel},
    }

"""
Análise da Fase 5 (adendo 3, commit 3004384, §5–§7).

Escrita, testada e commitada ANTES de qualquer métrica de desempenho da
Fase 5 ser aberta (cegamento registrado no changelog de 2026-09-29).

Entradas por execução (orçamento S ∈ {S1, S2}, braço ∈ {C, M25, M50},
seed ∈ {42, 123, 2024, 7, 31415}):
- recall  : `metrics/recall(B)` da ÚLTIMA linha do results.csv (ponto de
            máximo-F1 do Ultralytics; mesma definição da Fase 3);
- mAP50   : `metrics/mAP50(B)` da última linha;
- auc     : área sob a curva recall × passos (trapézio sobre as épocas
            1..N, com x = época × 337), dividida pelo intervalo de passos,
            isto é, o recall médio da trajetória;
- small   : recall do estrato small (< 32 px a 640), conf >= 0,25, IoU >= 0,5,
            casamento guloso (definição da F2 da Fase 3), sobre o last.pt.

Regra de decisão (§6.1), por contraste, com diferenças pareadas por seed
em pontos percentuais e t de Student com df = n − 1 = 4:
    IC95 inteiro < 0                  -> "sintetico_pior"
    IC95 inteiro > 0                  -> "sintetico_melhor"
    IC90 inteiro dentro de ±1,0 pp    -> "equivalente"   (TOST, α = 0,05)
    nenhum                            -> "inconclusivo"
DECISÃO DE IMPLEMENTAÇÃO (o adendo é silencioso sobre sobreposição;
fixada aqui antes de ver os dados): se o IC95 exclui 0 E o IC90 está
dentro da margem, o veredito é o da diferença (pior/melhor) e o campo
`tambem_dentro_da_margem` = True é reportado ao lado. Isso corresponde à
leitura "diferença estatisticamente detectável, mas menor que a margem
de relevância".

P13 (interação): "interacao_positiva" / "interacao_negativa" /
"interacao_nao_detectada", sem TOST (§6.4).

Subdimensionamento (§6.1): sinalizado quando o dp das diferenças
pareadas passa de 0,8 pp.
"""
from __future__ import annotations

import csv
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np

from .analise import _sf_f, _sf_t, _t_pareado

ORCAMENTOS = ("S1", "S2")
BRACOS = ("C", "M25", "M50")
SEEDS = (42, 123, 2024, 7, 31415)
PASSOS_POR_EPOCA = 337
MARGEM_PP = 1.0
LIMIAR_SUBDIMENSIONADO_PP = 0.8

# Fase 3, controle (real × 2, 150 épocas), recall val na época 150,
# publicado em docs/resultados_fase3.md. Usado SÓ na comparação de
# sanidade F3 (não pareada; protocolos diferentes).
CONTROLE_FASE3 = {42: 0.7017, 123: 0.7151, 2024: 0.6985}


# ---------------------------------------------------------------------------
# Leitura de results.csv
# ---------------------------------------------------------------------------

@dataclass
class MetricasExecucao:
    recall: float
    map50: float
    auc: float
    epoca_pico: int
    passo_pico: int
    recall_pico: float
    n_epocas: int
    small: float | None = None


def ler_results(caminho: Path) -> tuple[list[int], list[float], list[float]]:
    with open(caminho, newline="", encoding="utf-8") as f:
        leitor = csv.reader(f)
        cab = [c.strip() for c in next(leitor)]
        linhas = [dict(zip(cab, (v.strip() for v in r))) for r in leitor if r]
    epocas = [int(float(l["epoch"])) for l in linhas]
    recall = [float(l["metrics/recall(B)"]) for l in linhas]
    map50 = [float(l["metrics/mAP50(B)"]) for l in linhas]
    return epocas, recall, map50


def auc_normalizada(epocas: list[int], valores: list[float], passos_por_epoca: int = PASSOS_POR_EPOCA) -> float:
    """Trapézio sobre x = época × passos_por_epoca, dividido pelo intervalo de x."""
    if len(valores) < 2:
        return float(valores[0]) if valores else float("nan")
    x = np.asarray(epocas, dtype=float) * passos_por_epoca
    y = np.asarray(valores, dtype=float)
    area = float(np.sum((x[1:] - x[:-1]) * (y[1:] + y[:-1]) / 2.0))
    return area / float(x[-1] - x[0])


def metricas_de_results(caminho: Path, epocas_esperadas: int) -> MetricasExecucao:
    epocas, recall, map50 = ler_results(caminho)
    if len(epocas) != epocas_esperadas or epocas != list(range(1, epocas_esperadas + 1)):
        raise ValueError(f"{caminho}: épocas {epocas[:3]}…{epocas[-3:]} (n={len(epocas)}) != 1..{epocas_esperadas}")
    i_pico = int(np.argmax(recall))  # primeira ocorrência em empates
    return MetricasExecucao(
        recall=recall[-1], map50=map50[-1], auc=auc_normalizada(epocas, recall),
        epoca_pico=epocas[i_pico], passo_pico=epocas[i_pico] * PASSOS_POR_EPOCA,
        recall_pico=recall[i_pico], n_epocas=len(epocas),
    )


# ---------------------------------------------------------------------------
# Estatística
# ---------------------------------------------------------------------------

def t_quantil(prob: float, df: int) -> float:
    """Quantil da t de Student (prob em (0,5; 1)) por bisseção de _sf_t."""
    if not 0.5 < prob < 1.0:
        raise ValueError("prob deve estar em (0,5; 1)")
    alvo = 1.0 - prob
    lo, hi = 0.0, 1e3
    for _ in range(200):
        meio = (lo + hi) / 2
        if _sf_t(meio, df) > alvo:
            lo = meio
        else:
            hi = meio
    return (lo + hi) / 2


@dataclass
class ContrasteF5:
    nome: str
    familia: str
    tipo: str  # "diferenca" (§6.1) | "interacao" (§6.4) | "descritivo"
    por_seed_pp: dict[int, float]
    media_pp: float
    dp_pp: float
    ic95_pp: tuple[float, float]
    ic90_pp: tuple[float, float]
    t: float
    p: float
    p_tost: float | None
    d_cohen: float
    leave_one_seed_out_pp: dict[int, float]
    subdimensionado: bool
    veredito: str
    tambem_dentro_da_margem: bool = False
    p_holm: float | None = None
    nota: str = ""


def _cauda_superior(t: float, df: int) -> float:
    """P(T > t) para qualquer sinal de t (_sf_t da Fase 3 só é válida para t >= 0)."""
    return _sf_t(t, df) if t >= 0 else 1.0 - _sf_t(-t, df)


def _tost_p(media: float, se: float, df: int, margem: float) -> float:
    if se == 0:
        return 0.0 if abs(media) < margem else 1.0
    p_inf = _cauda_superior((media + margem) / se, df)   # H0: média <= −margem
    p_sup = _cauda_superior((margem - media) / se, df)   # H0: média >= +margem
    return max(p_inf, p_sup)


def contraste_f5(nome: str, familia: str, diffs_por_seed: dict[int, float], tipo: str = "diferenca",
                 margem_pp: float = MARGEM_PP, nota: str = "") -> ContrasteF5:
    """`diffs_por_seed` em FRAÇÃO (ex.: 0,012 = 1,2 pp)."""
    seeds = sorted(diffs_por_seed)
    d = np.array([diffs_por_seed[s] for s in seeds], dtype=float) * 100.0
    n, df = len(d), len(d) - 1
    media = float(d.mean())
    dp = float(d.std(ddof=1)) if n > 1 else 0.0
    se = dp / math.sqrt(n) if n > 1 else 0.0
    t95, t90 = t_quantil(0.975, df), t_quantil(0.95, df)
    ic95 = (media - t95 * se, media + t95 * se)
    ic90 = (media - t90 * se, media + t90 * se)
    t, p = _t_pareado(d)
    loo = {s: float(np.mean([v for o, v in zip(seeds, d) if o != s])) for s in seeds} if n > 2 else {}
    dentro = ic90[0] > -margem_pp and ic90[1] < margem_pp

    if tipo == "interacao":
        veredito = "interacao_positiva" if ic95[0] > 0 else "interacao_negativa" if ic95[1] < 0 else "interacao_nao_detectada"
        p_tost, dentro = None, False
    elif tipo == "diferenca":
        veredito = ("sintetico_pior" if ic95[1] < 0 else "sintetico_melhor" if ic95[0] > 0
                    else "equivalente" if dentro else "inconclusivo")
        p_tost = _tost_p(media, se, df, margem_pp)
    else:
        veredito, p_tost, dentro = "descritivo", _tost_p(media, se, df, margem_pp), dentro

    return ContrasteF5(
        nome=nome, familia=familia, tipo=tipo, por_seed_pp={s: float(v) for s, v in zip(seeds, d)},
        media_pp=media, dp_pp=dp, ic95_pp=ic95, ic90_pp=ic90, t=t, p=p, p_tost=p_tost,
        d_cohen=(media / dp) if dp > 0 else (math.inf if media else 0.0),
        leave_one_seed_out_pp=loo, subdimensionado=dp > LIMIAR_SUBDIMENSIONADO_PP,
        veredito=veredito, tambem_dentro_da_margem=bool(dentro and veredito in ("sintetico_pior", "sintetico_melhor")),
        nota=nota,
    )


def holm(contrastes: list[ContrasteF5]) -> None:
    validos = sorted((c for c in contrastes if not math.isnan(c.p)), key=lambda c: c.p)
    m, anterior = len(validos), 0.0
    for i, c in enumerate(validos):
        anterior = max(anterior, min(1.0, (m - i) * c.p))
        c.p_holm = anterior


@dataclass
class Anova2x3Bloco:
    ss: dict[str, float]
    df: dict[str, int]
    f: dict[str, float]
    p: dict[str, float]


def anova_2x3_bloco(y: dict[str, dict[str, dict[int, float]]]) -> Anova2x3Bloco:
    """ANOVA orçamento (2) × fração (3) com seed como bloco, desenho
    balanceado, somas de quadrados clássicas; y em fração -> SS em pp²."""
    orcs, brs = list(ORCAMENTOS), list(BRACOS)
    seeds = sorted(next(iter(next(iter(y.values())).values())))
    Y = np.array([[[y[o][b][s] * 100 for s in seeds] for b in brs] for o in orcs])  # (a, b, n)
    a, b, n = Y.shape
    g = Y.mean()
    ss_a = b * n * np.sum((Y.mean(axis=(1, 2)) - g) ** 2)
    ss_b = a * n * np.sum((Y.mean(axis=(0, 2)) - g) ** 2)
    ss_ab = n * np.sum((Y.mean(axis=2) - Y.mean(axis=(1, 2))[:, None] - Y.mean(axis=(0, 2))[None, :] + g) ** 2)
    ss_s = a * b * np.sum((Y.mean(axis=(0, 1)) - g) ** 2)
    ss_t = np.sum((Y - g) ** 2)
    ss_e = ss_t - ss_a - ss_b - ss_ab - ss_s
    df = {"orcamento": a - 1, "fracao": b - 1, "interacao": (a - 1) * (b - 1), "seed": n - 1}
    df["erro"] = a * b * n - 1 - sum(df.values())
    ss = {"orcamento": ss_a, "fracao": ss_b, "interacao": ss_ab, "seed": ss_s, "erro": ss_e, "total": ss_t}
    ms_e = ss_e / df["erro"]
    f = {k: (ss[k] / df[k]) / ms_e if ms_e > 0 else math.inf for k in ("orcamento", "fracao", "interacao", "seed")}
    p = {k: _sf_f(v, df[k], df["erro"]) if math.isfinite(v) else 0.0 for k, v in f.items()}
    return Anova2x3Bloco({k: float(v) for k, v in ss.items()}, df, {k: float(v) for k, v in f.items()}, p)


# ---------------------------------------------------------------------------
# Análise completa
# ---------------------------------------------------------------------------

Tabela = dict[str, dict[str, dict[int, float]]]  # [orcamento][braco][seed] -> fração


def _dif(t: Tabela, orc: str, a: str, b: str) -> dict[int, float]:
    return {s: t[orc][a][s] - t[orc][b][s] for s in t[orc][a]}


def analisar(recall: Tabela, map50: Tabela, auc: Tabela, small: Tabela,
             pico: dict[str, dict[str, dict[int, int]]] | None = None) -> dict:
    # --- F1 confirmatória ---
    p11 = contraste_f5("P11: M50 − C (S2)", "F1", _dif(recall, "S2", "M50", "C"))
    p12 = contraste_f5(
        "P12: contraste linear (−1, 0, +1)/2 em S2", "F1",
        {s: (recall["S2"]["M50"][s] - recall["S2"]["C"][s]) / 2 for s in SEEDS},
        nota="Com 3 doses equiespaçadas, o contraste linear (−1,0,+1) não usa M25: "
             "P12 = P11/2 por construção (mesmo t, mesmo p). Redundância do desenho lacrado, reportada, não corrigida.",
    )
    p13 = contraste_f5(
        "P13: (M50 − C)_S2 − (M50 − C)_S1", "F1",
        {s: (recall["S2"]["M50"][s] - recall["S2"]["C"][s]) - (recall["S1"]["M50"][s] - recall["S1"]["C"][s]) for s in SEEDS},
        tipo="interacao",
    )
    f1 = [p11, p12, p13]
    holm(f1)

    # --- F2 secundária ---
    f2 = [
        contraste_f5("F2a: P11 no estrato small", "F2", _dif(small, "S2", "M50", "C")),
        contraste_f5("F2b: P11 em mAP50", "F2", _dif(map50, "S2", "M50", "C")),
        contraste_f5("F2c: P11 na área sob a curva recall × passos", "F2", _dif(auc, "S2", "M50", "C")),
        contraste_f5("F2d: M50 − C (S1)", "F2", _dif(recall, "S1", "M50", "C")),
    ]
    holm(f2)

    # --- F3 exploratória ---
    f3 = [
        contraste_f5("F3a: M25 − M50 (S2)", "F3", _dif(recall, "S2", "M25", "M50"), tipo="descritivo"),
        contraste_f5("F3b: M25 − C (S2)", "F3", _dif(recall, "S2", "M25", "C"), tipo="descritivo"),
        contraste_f5("F3c: quadrático (C − 2·M25 + M50)/2 em S2", "F3",
                     {s: (recall["S2"]["C"][s] - 2 * recall["S2"]["M25"][s] + recall["S2"]["M50"][s]) / 2 for s in SEEDS},
                     tipo="descritivo",
                     nota="Curvatura da dose-resposta; acrescentado após a lacração e antes de qualquer dado, "
                          "porque o contraste linear lacrado (P12) não usa M25."),
        contraste_f5("F3d: quadrático em S1", "F3",
                     {s: (recall["S1"]["C"][s] - 2 * recall["S1"]["M25"][s] + recall["S1"]["M50"][s]) / 2 for s in SEEDS},
                     tipo="descritivo"),
    ]
    c_s2 = [recall["S2"]["C"][s] for s in SEEDS]
    sanidade = {
        "C_S2_media": float(np.mean(c_s2)),
        "controle_fase3_media": float(np.mean(list(CONTROLE_FASE3.values()))),
        "diferenca_pp_nao_pareada": float((np.mean(c_s2) - np.mean(list(CONTROLE_FASE3.values()))) * 100),
        "nota": "Não pareada; C(S2) = real × 4, 75 épocas, 25.275 passos; controle Fase 3 = real × 2, 150 épocas, 25.350 passos.",
    }
    medias = {m: {o: {b: float(np.mean([t[o][b][s] for s in SEEDS])) for b in BRACOS} for o in ORCAMENTOS}
              for m, t in (("recall", recall), ("map50", map50), ("auc", auc), ("small", small))}
    pico_resumo = None
    if pico is not None:
        pico_resumo = {o: {b: {"passo_pico_por_seed": pico[o][b],
                               "passo_pico_medio": float(np.mean(list(pico[o][b].values())))} for b in BRACOS}
                       for o in ORCAMENTOS}
    return {
        "F1": [asdict(c) for c in f1],
        "F2": [asdict(c) for c in f2],
        "F3": [asdict(c) for c in f3],
        "F3_sanidade_controle_fase3": sanidade,
        "F3_pico": pico_resumo,
        "anova_2x3_bloco_seed": asdict(anova_2x3_bloco(recall)),
        "medias": medias,
    }


def tabela_markdown(resultado: dict) -> str:
    def fmt(c):
        ic = c["ic95_pp"]
        extra = " (dentro da margem ±1 pp)" if c["tambem_dentro_da_margem"] else ""
        sub = " ⚠️ subdimensionado" if c["subdimensionado"] else ""
        holm_ = f"{c['p_holm']:.3f}" if c["p_holm"] is not None else "—"
        tost = f"{c['p_tost']:.3f}" if c["p_tost"] is not None else "—"
        seeds = ", ".join(f"{v:+.2f}" for v in c["por_seed_pp"].values())
        return (f"| {c['nome']} | {c['media_pp']:+.2f} | [{ic[0]:+.2f}, {ic[1]:+.2f}] | {seeds} | "
                f"{c['p']:.3f} | {holm_} | {tost} | **{c['veredito']}**{extra}{sub} |")
    cab = ("| Contraste | média (pp) | IC95 | por seed (pp) | p | p Holm | p TOST | veredito |\n"
           "|---|---|---|---|---|---|---|---|")
    partes = []
    for fam in ("F1", "F2", "F3"):
        partes.append(f"\n### {fam}\n\n{cab}\n" + "\n".join(fmt(c) for c in resultado[fam]))
    return "\n".join(partes)

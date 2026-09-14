"""
Análise SHAP do modelo substituto (§5.5 do plano).

Três saídas, todas em CPU:
1. Ranking por |SHAP| médio, com DIREÇÃO do efeito (correlação entre o
   valor da feature e o seu valor SHAP: positiva = feature maior ->
   mais provável acertar).
2. Agregação por CLUSTER de features colineares (§5.5): a importância
   de um cluster é a soma das importâncias das suas features -- evita
   que duas medidas da mesma coisa (ex.: area_caixa_norm e
   menor_lado_caixa_px, r=0,82) dividam entre si um sinal que, somado,
   seria o mais importante.
3. Estabilidade por bootstrap POR GRUPO (§9, portão da Fase 2):
   reamostra grupos geométricos com reposição (nunca linhas -- as 20
   variações de uma caixa não são independentes), retreina, recalcula o
   ranking, e mede quão estável é a posição de cada feature.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import shap

from .modelo import criar_modelo, FEATURES_PRINCIPAIS, ALVO, GRUPO

CLUSTERS_PADRAO = {
    "tamanho_caixa": ["area_caixa_norm", "menor_lado_caixa_px"],
}


def calcular_shap(modelo, X: np.ndarray) -> np.ndarray:
    """Valores SHAP (n_amostras x n_features) da classe positiva."""
    explainer = shap.TreeExplainer(modelo)
    sv = explainer.shap_values(X)
    sv = np.asarray(sv)
    if sv.ndim == 3:  # alguns backends retornam (n, features, classes)
        sv = sv[:, :, -1]
    return sv


def ranking_importancia(shap_values: np.ndarray, X: np.ndarray, features: list[str]) -> pd.DataFrame:
    """Uma linha por feature: |SHAP| médio, posição no ranking, e direção."""
    importancia = np.abs(shap_values).mean(axis=0)
    direcoes = []
    for j in range(len(features)):
        x = X[:, j]
        s = shap_values[:, j]
        if np.std(x) == 0 or np.std(s) == 0:
            direcoes.append(0.0)
        else:
            direcoes.append(float(np.corrcoef(x, s)[0, 1]))
    df = pd.DataFrame({
        "feature": features,
        "importancia_shap": importancia,
        "direcao": direcoes,
    }).sort_values("importancia_shap", ascending=False).reset_index(drop=True)
    df["posicao"] = np.arange(1, len(df) + 1)
    return df


def importancia_por_cluster(
    ranking: pd.DataFrame, clusters: dict[str, list[str]] | None = None,
) -> pd.DataFrame:
    """Soma a importância das features de cada cluster; features fora de
    qualquer cluster viram clusters unitários. Retorna ranking por cluster."""
    clusters = clusters if clusters is not None else CLUSTERS_PADRAO
    imp = dict(zip(ranking["feature"], ranking["importancia_shap"]))
    agrupadas = {f for fs in clusters.values() for f in fs}

    linhas = []
    for nome, fs in clusters.items():
        presentes = [f for f in fs if f in imp]
        if presentes:
            linhas.append({"cluster": nome, "features": presentes,
                           "importancia_shap": float(sum(imp[f] for f in presentes))})
    for f, v in imp.items():
        if f not in agrupadas:
            linhas.append({"cluster": f, "features": [f], "importancia_shap": float(v)})

    df = pd.DataFrame(linhas).sort_values("importancia_shap", ascending=False).reset_index(drop=True)
    df["posicao"] = np.arange(1, len(df) + 1)
    return df


@dataclass
class EstabilidadeBootstrap:
    n_reamostras: int
    posicao_media: dict[str, float]
    posicao_desvio: dict[str, float]
    frequencia_top_k: dict[str, float]
    k: int


def estabilidade_bootstrap_por_grupo(
    df: pd.DataFrame,
    features: list[str] | None = None,
    alvo: str = ALVO,
    grupo: str = GRUPO,
    n_reamostras: int = 30,
    k: int = 5,
    seed: int = 42,
) -> EstabilidadeBootstrap:
    """Reamostra GRUPOS com reposição, retreina o modelo, recalcula o
    ranking SHAP. Mede, para cada feature, a posição média/desvio no
    ranking e a frequência com que fica no top-k."""
    features = features or FEATURES_PRINCIPAIS
    rng = np.random.default_rng(seed)
    grupos_unicos = df[grupo].unique()
    posicoes: dict[str, list[int]] = {f: [] for f in features}

    for _ in range(n_reamostras):
        sorteio = rng.choice(grupos_unicos, size=len(grupos_unicos), replace=True)
        # concatena as linhas de cada grupo sorteado (com repetição, se sorteado mais de uma vez)
        partes = [df[df[grupo] == g] for g in sorteio]
        amostra = pd.concat(partes, ignore_index=True)

        X = amostra[features].to_numpy(dtype=float)
        y = amostra[alvo].to_numpy(dtype=int)
        modelo = criar_modelo(seed=int(rng.integers(0, 2**31 - 1)))
        modelo.fit(X, y)
        sv = calcular_shap(modelo, X)
        rk = ranking_importancia(sv, X, features)
        for f, p in zip(rk["feature"], rk["posicao"]):
            posicoes[f].append(int(p))

    return EstabilidadeBootstrap(
        n_reamostras=n_reamostras,
        posicao_media={f: float(np.mean(p)) for f, p in posicoes.items()},
        posicao_desvio={f: float(np.std(p, ddof=1)) if len(p) > 1 else 0.0 for f, p in posicoes.items()},
        frequencia_top_k={f: float(np.mean([pp <= k for pp in p])) for f, p in posicoes.items()},
        k=k,
    )

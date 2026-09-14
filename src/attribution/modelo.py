"""
Modelo substituto do Estágio A (§5.4 do plano): gradient boosting
prevendo o alvo binário (acerto_votacao) a partir das features de
composição, com validação cruzada POR GRUPO (grupo_geometrico_id) e
AUC-PR como métrica de portão.

Decisões pré-registradas em 2026-09-14 (antes de qualquer resultado):
- Validação por GroupKFold sobre `grupo_geometrico_id`, nunca por linha
  -- as 20 variações da mesma caixa compartilham geometria idêntica
  (§5.1), e um split por linha vazaria informação de grupo entre treino
  e teste, inflando o desempenho.
- Piso do portão: AUC-PR média (validação cruzada) >= 0,78. A taxa base
  de acerto é 0,702, então um modelo "chutando a majoritária" tem AUC-PR
  ~0,70; o piso exige ganho de ~8 pontos sobre o acaso para que o SHAP
  seja digno de leitura. Abaixo disso, revisar o alvo (§9, Fase 2), não
  forçar interpretação.
- `fonte` NÃO entra no modelo principal -- entra só num segundo modelo,
  para o teste de mediação de P3 (importância de `fonte` com e sem as
  features mediadoras).
- `coerencia_escala_pos` excluída (redundante exata com log área neste
  domínio, ver changelog 2026-09-14).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import GroupKFold

FEATURES_PRINCIPAIS = [
    "log_fator_reescala",
    "upsample",
    "distorcao_aspect",
    "crop_menor_lado_original_px",
    "area_caixa_norm",
    "menor_lado_caixa_px",
    "pos_v",
    "pos_h",
    "aspect_caixa",
    "nitidez",
    "contraste",
    "brilho_medio",
    "cobertura_mascara",
]

ALVO = "acerto_votacao"
GRUPO = "grupo_geometrico_id"
PISO_AUC_PR = 0.78  # pré-registrado -- não ajustar depois de ver o resultado


@dataclass
class ResultadoValidacao:
    auc_pr_por_fold: list[float]
    auc_roc_por_fold: list[float]
    taxa_base: float
    n_folds: int
    passou_portao: bool
    piso: float = PISO_AUC_PR

    @property
    def auc_pr_media(self) -> float:
        return float(np.mean(self.auc_pr_por_fold))

    @property
    def auc_pr_desvio(self) -> float:
        return float(np.std(self.auc_pr_por_fold, ddof=1)) if len(self.auc_pr_por_fold) > 1 else 0.0

    @property
    def auc_roc_media(self) -> float:
        return float(np.mean(self.auc_roc_por_fold))


def criar_modelo(seed: int = 42) -> HistGradientBoostingClassifier:
    """Configuração fixa e modesta -- o objetivo é um substituto
    interpretável, não um classificador ótimo. Hiperparâmetros pequenos
    reduzem o risco de o SHAP refletir sobreajuste em vez de estrutura."""
    return HistGradientBoostingClassifier(
        max_iter=300,
        learning_rate=0.05,
        max_depth=4,
        min_samples_leaf=50,
        l2_regularization=1.0,
        random_state=seed,
    )


def validar_por_grupo(
    df: pd.DataFrame,
    features: list[str] | None = None,
    alvo: str = ALVO,
    grupo: str = GRUPO,
    n_folds: int = 5,
    seed: int = 42,
    piso: float = PISO_AUC_PR,
) -> ResultadoValidacao:
    """Validação cruzada por grupo. Retorna AUC-PR e AUC-ROC por fold e
    o veredito do portão."""
    features = features or FEATURES_PRINCIPAIS
    X = df[features].to_numpy(dtype=float)
    y = df[alvo].to_numpy(dtype=int)
    grupos = df[grupo].to_numpy()

    gkf = GroupKFold(n_splits=n_folds)
    auc_pr, auc_roc = [], []
    for treino_idx, teste_idx in gkf.split(X, y, grupos):
        modelo = criar_modelo(seed)
        modelo.fit(X[treino_idx], y[treino_idx])
        prob = modelo.predict_proba(X[teste_idx])[:, 1]
        auc_pr.append(float(average_precision_score(y[teste_idx], prob)))
        auc_roc.append(float(roc_auc_score(y[teste_idx], prob)))

    media = float(np.mean(auc_pr))
    return ResultadoValidacao(
        auc_pr_por_fold=auc_pr,
        auc_roc_por_fold=auc_roc,
        taxa_base=float(y.mean()),
        n_folds=n_folds,
        passou_portao=media >= piso,
        piso=piso,
    )


def treinar_modelo_final(
    df: pd.DataFrame,
    features: list[str] | None = None,
    alvo: str = ALVO,
    seed: int = 42,
) -> HistGradientBoostingClassifier:
    """Modelo em TODOS os dados, para o SHAP -- só faz sentido chamar
    depois do portão da validação por grupo ter passado."""
    features = features or FEATURES_PRINCIPAIS
    modelo = criar_modelo(seed)
    modelo.fit(df[features].to_numpy(dtype=float), df[alvo].to_numpy(dtype=int))
    return modelo

from .alvo import construir_alvo
from .features import (
    calcular_features_geometricas,
    ajustar_regressao_escala_posicao,
    caixas_reais_do_alvo,
    calcular_features_intrinsecas,
)
from .tabela import construir_tabela_features, construir_indice_crops

__all__ = [
    "construir_alvo",
    "calcular_features_geometricas",
    "ajustar_regressao_escala_posicao",
    "caixas_reais_do_alvo",
    "calcular_features_intrinsecas",
    "construir_tabela_features",
    "construir_indice_crops",
]
from .modelo import (
    validar_por_grupo, treinar_modelo_final, criar_modelo,
    FEATURES_PRINCIPAIS, ALVO, GRUPO, PISO_AUC_PR, ResultadoValidacao,
)
__all__ += [
    "validar_por_grupo", "treinar_modelo_final", "criar_modelo",
    "FEATURES_PRINCIPAIS", "ALVO", "GRUPO", "PISO_AUC_PR", "ResultadoValidacao",
]
from .shap_analise import (
    calcular_shap, ranking_importancia, importancia_por_cluster,
    estabilidade_bootstrap_por_grupo, CLUSTERS_PADRAO, EstabilidadeBootstrap,
)
__all__ += [
    "calcular_shap", "ranking_importancia", "importancia_por_cluster",
    "estabilidade_bootstrap_por_grupo", "CLUSTERS_PADRAO", "EstabilidadeBootstrap",
]
from .controle_grupo import adicionar_taxa_grupo_loo, features_controladas, FEATURES_CROP, COVARIAVEL_GRUPO
__all__ += ["adicionar_taxa_grupo_loo", "features_controladas", "FEATURES_CROP", "COVARIAVEL_GRUPO"]

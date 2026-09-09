from .target_profile import (
    perfilar_dataset,
    classificar_tamanho_letterbox,
    CaixaPerfil,
    LIMIAR_SMALL_PX,
    LIMIAR_MEDIUM_PX,
    EVAL_SIZE_PADRAO,
)
from .source_profile import perfilar_fonte, tabela_decisao_min_dim_px
from .coverage_check import (
    obter_tamanhos_absolutos_alvo,
    simular_compatibilidade_escala,
    ResultadoSimulacaoEscala,
)

__all__ = [
    "perfilar_dataset",
    "classificar_tamanho_letterbox",
    "CaixaPerfil",
    "LIMIAR_SMALL_PX",
    "LIMIAR_MEDIUM_PX",
    "EVAL_SIZE_PADRAO",
    "perfilar_fonte",
    "tabela_decisao_min_dim_px",
    "obter_tamanhos_absolutos_alvo",
    "simular_compatibilidade_escala",
    "ResultadoSimulacaoEscala",
]

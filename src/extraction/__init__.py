from .dedup_roboflow import (
    deduplicar_por_base,
    identificar_base_roboflow,
    ResultadoDeduplicacao,
)
from .quality_filter import FiltroConfig, avaliar_crop, ResultadoAvaliacao
from .quality_manifest import (
    filtrar_pool_de_crops,
    carregar_coberturas_do_manifesto_extracao,
    LinhaManifestoExtracao,
)
from .extrair_crops_yolo import (
    extrair_crops_de_yolo,
    identificar_video_id,
    LinhaExtracaoYolo,
)
from .extrair_crops_voc import extrair_crops_de_voc, LinhaExtracaoVoc
from .extrair_crops_csv_abo import (
    extrair_crops_de_csv_abo,
    LinhaExtracaoCsvAbo,
    NomeBaseAmbiguo,
)

__all__ = [
    "deduplicar_por_base",
    "identificar_base_roboflow",
    "ResultadoDeduplicacao",
    "FiltroConfig",
    "avaliar_crop",
    "ResultadoAvaliacao",
    "filtrar_pool_de_crops",
    "carregar_coberturas_do_manifesto_extracao",
    "LinhaManifestoExtracao",
    "extrair_crops_de_yolo",
    "identificar_video_id",
    "LinhaExtracaoYolo",
    "extrair_crops_de_voc",
    "LinhaExtracaoVoc",
    "extrair_crops_de_csv_abo",
    "LinhaExtracaoCsvAbo",
    "NomeBaseAmbiguo",
]

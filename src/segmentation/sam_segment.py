"""
Segmentação para isolar o objeto do fundo antes de recortar (mitiga o
risco de "shortcut learning" via borda de colagem visível -- Geirhos et
al., 2020, "Shortcut Learning in Deep Neural Networks", Nature Machine
Intelligence, 2(11):665-673 -- ver docs/CHANGELOG_metodologico.md).

Princípio de desenho: a segmentação SEMPRE roda sobre a IMAGEM ORIGINAL
(nunca sobre um crop já recortado) -- o SAM precisa de contexto de fundo
ao redor da caixa para traçar a fronteira do objeto com precisão, e rodar
sobre um crop já minúsculo forçaria upsampling que borra a imagem antes da
segmentação começar.

Interface `Segmentador`: qualquer objeto com um método
`segmentar(imagem_rgb, caixa) -> mascara_bool` serve. Isso permite testar
toda a lógica de aplicação de máscara / recorte / cálculo de cobertura com
um segmentador falso (sem GPU, sem pesos do SAM) -- e trocar por
`SegmentadorSAM` de verdade no ambiente com GPU sem mudar mais nada.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np
from PIL import Image


class Segmentador(Protocol):
    def segmentar(self, imagem_rgb: np.ndarray, caixa: tuple[int, int, int, int]) -> np.ndarray:
        """Retorna uma máscara booleana (mesma altura/largura de imagem_rgb),
        True onde pertence ao objeto dentro da região da caixa."""
        ...


@dataclass
class ResultadoSegmentacao:
    crop_rgba: Image.Image
    cobertura_mascara: float  # fração da área da caixa coberta pela máscara


def aplicar_mascara_e_recortar(
    imagem_rgb: np.ndarray, caixa: tuple[int, int, int, int], mascara: np.ndarray,
) -> ResultadoSegmentacao:
    """Aplica uma máscara booleana (do tamanho da imagem inteira) e recorta
    pela caixa, produzindo um crop RGBA com fundo transparente fora da
    máscara. Calcula a cobertura (fração da área da caixa coberta pela
    máscara) -- alimenta diretamente FiltroConfig.min_cobertura_mascara
    (já existente em src/extraction/quality_filter.py desde a tarefa -1.3).
    """
    x0, y0, x1, y1 = caixa
    altura_img, largura_img = imagem_rgb.shape[:2]
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(largura_img, x1), min(altura_img, y1)

    recorte_rgb = imagem_rgb[y0:y1, x0:x1]
    recorte_mascara = mascara[y0:y1, x0:x1]

    area_caixa = recorte_mascara.size
    cobertura = float(recorte_mascara.sum()) / area_caixa if area_caixa > 0 else 0.0

    alpha = (recorte_mascara * 255).astype(np.uint8)
    rgba = np.dstack([recorte_rgb, alpha])
    crop_rgba = Image.fromarray(rgba, mode="RGBA")

    return ResultadoSegmentacao(crop_rgba=crop_rgba, cobertura_mascara=cobertura)


class SegmentadorSAM:
    """Wrapper do Segment Anything Model (Meta AI) com prompt de caixa.

    Referência: Kirillov, A. et al. (2023). "Segment Anything." ICCV 2023.

    Import de `segment_anything`/`torch` é tardio (dentro de `carregar`),
    para que o restante deste módulo (interface, aplicação de máscara,
    cálculo de cobertura) não dependa de GPU nem dessas bibliotecas
    pesadas, e possa ser testado normalmente em qualquer ambiente.
    """

    def __init__(self, predictor):
        self._predictor = predictor
        self._imagem_atual_id: int | None = None

    @classmethod
    def carregar(cls, checkpoint_path: str, model_type: str = "vit_b", device: str = "cuda") -> "SegmentadorSAM":
        from segment_anything import sam_model_registry, SamPredictor  # import tardio

        sam = sam_model_registry[model_type](checkpoint=checkpoint_path)
        sam.to(device=device)
        predictor = SamPredictor(sam)
        return cls(predictor)

    def segmentar(self, imagem_rgb: np.ndarray, caixa: tuple[int, int, int, int]) -> np.ndarray:
        # cacheia o encoding da imagem -- várias caixas da mesma imagem não
        # devem re-rodar o encoder a cada chamada (é a parte cara do SAM)
        if self._imagem_atual_id != id(imagem_rgb):
            self._predictor.set_image(imagem_rgb)
            self._imagem_atual_id = id(imagem_rgb)

        import numpy as _np
        caixa_arr = _np.array(caixa)
        mascaras, scores, _ = self._predictor.predict(box=caixa_arr, multimask_output=True)
        melhor = mascaras[scores.argmax()]
        return melhor.astype(bool)

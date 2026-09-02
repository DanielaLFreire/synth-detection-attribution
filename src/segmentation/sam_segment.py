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
    """Wrapper do Segment Anything Model 1 (Meta AI) com prompt de caixa.

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


def _calcular_iou(caixa_a: tuple[float, float, float, float], caixa_b: tuple[float, float, float, float]) -> float:
    """IoU (Intersection over Union) entre duas caixas (x0,y0,x1,y1).
    Função pura, sem dependência de SAM/torch -- totalmente testável."""
    ax0, ay0, ax1, ay1 = caixa_a
    bx0, by0, bx1, by1 = caixa_b

    ix0, iy0 = max(ax0, bx0), max(ay0, by0)
    ix1, iy1 = min(ax1, bx1), min(ay1, by1)
    largura_inter = max(0.0, ix1 - ix0)
    altura_inter = max(0.0, iy1 - iy0)
    area_inter = largura_inter * altura_inter

    area_a = max(0.0, ax1 - ax0) * max(0.0, ay1 - ay0)
    area_b = max(0.0, bx1 - bx0) * max(0.0, by1 - by0)
    area_uniao = area_a + area_b - area_inter

    return area_inter / area_uniao if area_uniao > 0 else 0.0


def indice_melhor_iou(
    caixas_candidatas: list[tuple[float, float, float, float]],
    caixa_alvo: tuple[float, float, float, float],
    iou_minimo: float = 0.1,
) -> int | None:
    """Retorna o índice, em `caixas_candidatas`, da caixa com maior IoU
    contra `caixa_alvo`, ou None se nenhuma candidata atingir `iou_minimo`
    (nesse caso, nenhuma instância detectada corresponde de forma confiável
    à caixa de anotação conhecida -- melhor não segmentar do que segmentar
    o objeto errado)."""
    if not caixas_candidatas:
        return None
    ious = [_calcular_iou(c, caixa_alvo) for c in caixas_candidatas]
    melhor_idx = max(range(len(ious)), key=lambda i: ious[i])
    return melhor_idx if ious[melhor_idx] >= iou_minimo else None


def _caixa_absoluta_para_cxcywh_normalizado(
    caixa: tuple[float, float, float, float], largura_img: int, altura_img: int,
) -> list[float]:
    """Converte (x0,y0,x1,y1) em pixels absolutos para [cx,cy,w,h]
    normalizado em [0,1] -- formato exigido por
    Sam3Processor.add_geometric_prompt (confirmado lendo o código-fonte
    real de sam3/model/sam3_image_processor.py, não documentação
    de terceiros). Função pura, testável sem SAM."""
    x0, y0, x1, y1 = caixa
    cx = (x0 + x1) / 2 / largura_img
    cy = (y0 + y1) / 2 / altura_img
    w = (x1 - x0) / largura_img
    h = (y1 - y0) / altura_img
    return [cx, cy, w, h]


class SegmentadorSAM3:
    """Wrapper do Segment Anything Model 3 (Meta AI), com prompt de CAIXA.

    Referência: Carion, N. et al. (2025). "SAM 3: Segment Anything with
    Concepts." arXiv:2511.16719.

    CORREÇÃO REGISTRADA (2026-09-01): uma versão anterior deste wrapper
    usava prompt de texto + correspondência por IoU, porque não havia sido
    possível confirmar, a partir de documentação de terceiros, um método
    de prompt de caixa equivalente ao SamPredictor.predict(box=...) do
    SAM 1/2. Ao clonar o repositório oficial (facebookresearch/sam3) e ler
    `sam3/model/sam3_image_processor.py` diretamente, confirmou-se que
    `Sam3Processor.add_geometric_prompt(box, label, state)` existe e faz
    exatamente isso -- prompt de caixa, formato [cx,cy,w,h] normalizado em
    [0,1], funciona sem exigir prompt de texto (usa um prompt de texto
    "visual" interno como placeholder quando nenhum foi definido). Ver
    docs/CHANGELOG_metodologico.md para o registro completo da correção.

    Detalhe de uso que exige cuidado (confirmado no código-fonte):
    `add_geometric_prompt` ACUMULA caixas no estado
    (`geometric_prompt.append_boxes`) em vez de substituir -- para
    processar múltiplas caixas da MESMA imagem, é preciso chamar
    `reset_all_prompts(state)` entre uma caixa e outra, preservando o
    encoding caro da imagem (`state["backbone_out"]`, não afetado pelo
    reset) mas limpando o prompt geométrico anterior.
    """

    def __init__(self, processor):
        self._processor = processor
        self._estado_atual = None
        self._imagem_atual_id: int | None = None

    @classmethod
    def carregar(cls, bpe_path: str | None = None) -> "SegmentadorSAM3":
        """Carrega o modelo SAM 3 para segmentação por imagem.

        `bpe_path`: caminho explícito para o vocabulário BPE
        (`assets/bpe_simple_vocab_16e6.txt.gz`, dentro do repositório
        `facebookresearch/sam3` clonado). PRECISA ser fornecido quando o
        pacote foi instalado em modo editável (`pip install -e .`) --
        nesse modo, `build_sam3_image_model(bpe_path=None)` tenta
        descobrir o caminho sozinho via `pkg_resources.resource_filename`,
        que falha com `TypeError: expected str, bytes or os.PathLike
        object, not NoneType` porque a instalação editável em Python
        3.13+/setuptools recentes deixa `sam3.__file__` como None -- bug
        conhecido da interação entre `pkg_resources` (biblioteca legada) e
        instalação editável via PEP 660, não um bug do nosso código. Ver
        docs/CHANGELOG_metodologico.md (2026-09-02) para o registro
        completo.

        Exemplo: se você clonou o sam3 em `/content/sam3`, passe
        `bpe_path="/content/sam3/sam3/assets/bpe_simple_vocab_16e6.txt.gz"`.
        """
        from sam3.model_builder import build_sam3_image_model  # import tardio
        from sam3.model.sam3_image_processor import Sam3Processor

        model = build_sam3_image_model(bpe_path=bpe_path)
        processor = Sam3Processor(model)
        return cls(processor)

    def segmentar(self, imagem_rgb: np.ndarray, caixa: tuple[int, int, int, int]) -> np.ndarray:
        import torch
        from PIL import Image as _PILImage

        altura_img, largura_img = imagem_rgb.shape[:2]

        # O SAM 3 exige rodar sob autocast bfloat16 -- confirmado nos seis
        # notebooks de exemplo oficiais (facebookresearch/sam3/examples/),
        # todos chamam torch.autocast("cuda", dtype=torch.bfloat16) logo
        # após carregar o modelo. Sem isso, partes do modelo (backbone
        # visual) operam em bfloat16 enquanto as ativações de entrada ficam
        # em float32, causando RuntimeError de dtype incompatível numa
        # camada Linear interna. Aqui o contexto envolve só as chamadas de
        # inferência (não fica aberto indefinidamente, diferente do padrão
        # usado nos notebooks, que é aceitável em notebook mas não numa
        # biblioteca).
        with torch.autocast("cuda", dtype=torch.bfloat16):
            if self._imagem_atual_id != id(imagem_rgb):
                imagem_pil = _PILImage.fromarray(imagem_rgb)
                self._estado_atual = self._processor.set_image(imagem_pil)
                self._imagem_atual_id = id(imagem_rgb)
            else:
                # mesma imagem, nova caixa -- limpa o prompt geométrico anterior
                # (acumulativo por padrão), mantendo o encoding da imagem em cache
                self._processor.reset_all_prompts(self._estado_atual)

            box_normalizada = _caixa_absoluta_para_cxcywh_normalizado(caixa, largura_img, altura_img)

            self._estado_atual = self._processor.add_geometric_prompt(
                box=box_normalizada, label=True, state=self._estado_atual,
            )

            mascaras = self._estado_atual.get("masks")
            caixas_retornadas = self._estado_atual.get("boxes")

        if mascaras is None or len(mascaras) == 0:
            return np.zeros((altura_img, largura_img), dtype=bool)

        # múltiplas instâncias podem passar do limiar de confiança mesmo
        # com prompt de caixa -- escolhe a de maior IoU contra a caixa
        # que pedimos, por segurança (função já testada isoladamente)
        caixas_lista = [tuple(c.tolist()) for c in caixas_retornadas]
        idx = indice_melhor_iou(caixas_lista, tuple(caixa), iou_minimo=0.1)
        if idx is None:
            return np.zeros((altura_img, largura_img), dtype=bool)

        mascara = mascaras[idx]
        mascara_np = mascara.squeeze().cpu().numpy() if hasattr(mascara, "cpu") else np.asarray(mascara).squeeze()
        return mascara_np.astype(bool)

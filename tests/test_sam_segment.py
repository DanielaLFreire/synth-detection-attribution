"""Testes do módulo de segmentação -- usa um segmentador FALSO (elipse
sintética), sem depender de GPU nem dos pesos reais do SAM. A lógica
testada aqui (aplicar máscara, recortar, calcular cobertura) é exatamente
a mesma que roda com o SegmentadorSAM real; só a fonte da máscara muda."""
from __future__ import annotations

import numpy as np
import pytest

from src.segmentation import aplicar_mascara_e_recortar


class SegmentadorFalsoRetanguloCheio:
    """Segmentador de teste: marca TODA a caixa como objeto (cobertura=1.0).
    Útil para confirmar que, no caso trivial, o resultado é equivalente ao
    recorte retangular antigo."""
    def segmentar(self, imagem_rgb, caixa):
        mascara = np.zeros(imagem_rgb.shape[:2], dtype=bool)
        x0, y0, x1, y1 = caixa
        mascara[y0:y1, x0:x1] = True
        return mascara


class SegmentadorFalsoMetadeDaCaixa:
    """Segmentador de teste: marca só a metade esquerda da caixa como
    objeto -- simula um objeto que não preenche toda a bounding box
    (situação realista: caixa retangular ao redor de um casco alongado)."""
    def segmentar(self, imagem_rgb, caixa):
        mascara = np.zeros(imagem_rgb.shape[:2], dtype=bool)
        x0, y0, x1, y1 = caixa
        meio = x0 + (x1 - x0) // 2
        mascara[y0:y1, x0:meio] = True
        return mascara


def _imagem_sintetica(largura=200, altura=100):
    return (np.random.rand(altura, largura, 3) * 255).astype(np.uint8)


def test_cobertura_total_quando_mascara_preenche_toda_a_caixa():
    imagem = _imagem_sintetica()
    caixa = (50, 20, 100, 60)  # 50x40 px
    seg = SegmentadorFalsoRetanguloCheio()
    mascara = seg.segmentar(imagem, caixa)

    resultado = aplicar_mascara_e_recortar(imagem, caixa, mascara)
    assert resultado.cobertura_mascara == 1.0
    assert resultado.crop_rgba.mode == "RGBA"
    assert resultado.crop_rgba.size == (50, 40)  # largura, altura


def test_cobertura_parcial_quando_mascara_e_metade_da_caixa():
    imagem = _imagem_sintetica()
    caixa = (50, 20, 100, 60)
    seg = SegmentadorFalsoMetadeDaCaixa()
    mascara = seg.segmentar(imagem, caixa)

    resultado = aplicar_mascara_e_recortar(imagem, caixa, mascara)
    assert resultado.cobertura_mascara == pytest.approx(0.5)


def test_pixels_fora_da_mascara_ficam_transparentes():
    imagem = _imagem_sintetica()
    caixa = (0, 0, 40, 40)
    seg = SegmentadorFalsoMetadeDaCaixa()
    mascara = seg.segmentar(imagem, caixa)

    resultado = aplicar_mascara_e_recortar(imagem, caixa, mascara)
    arr = np.array(resultado.crop_rgba)
    canal_alpha = arr[:, :, 3]

    # metade esquerda do crop (dentro da máscara) deve ser opaca (alpha=255)
    assert (canal_alpha[:, :20] == 255).all()
    # metade direita (fora da máscara) deve ser transparente (alpha=0)
    assert (canal_alpha[:, 20:] == 0).all()


def test_recorte_respeita_limites_da_imagem_quando_caixa_extrapola():
    """Caixa que extrapola a borda da imagem -- deve ser recortada aos
    limites reais, não quebrar."""
    imagem = _imagem_sintetica(largura=100, altura=100)
    caixa = (80, 80, 150, 150)  # extrapola para além de 100x100
    mascara = np.ones(imagem.shape[:2], dtype=bool)

    resultado = aplicar_mascara_e_recortar(imagem, caixa, mascara)
    assert resultado.crop_rgba.size == (20, 20)  # 100-80=20 nos dois eixos


# --------------------------------------------------------------------------
# Testes de indice_melhor_iou -- lógica central do SegmentadorSAM3 (o
# casamento por IoU entre instâncias detectadas por texto e a caixa
# de anotação conhecida). Totalmente testável sem SAM/GPU.
# --------------------------------------------------------------------------

from src.segmentation import indice_melhor_iou


def test_indice_melhor_iou_escolhe_caixa_com_maior_sobreposicao():
    caixa_alvo = (100, 100, 200, 200)
    candidatas = [
        (500, 500, 600, 600),   # sem sobreposição -- objeto errado
        (100, 100, 200, 200),   # sobreposição perfeita -- objeto certo
        (150, 150, 250, 250),   # sobreposição parcial
    ]
    idx = indice_melhor_iou(candidatas, caixa_alvo)
    assert idx == 1


def test_indice_melhor_iou_retorna_none_quando_nenhuma_bate_o_minimo():
    caixa_alvo = (100, 100, 200, 200)
    candidatas = [(500, 500, 600, 600), (700, 700, 800, 800)]
    idx = indice_melhor_iou(candidatas, caixa_alvo, iou_minimo=0.1)
    assert idx is None


def test_indice_melhor_iou_lista_vazia_retorna_none():
    assert indice_melhor_iou([], (100, 100, 200, 200)) is None


def test_indice_melhor_iou_respeita_limiar_minimo_customizado():
    caixa_alvo = (0, 0, 100, 100)
    # sobreposição de 50x50 numa caixa de 100x100 = IoU baixo (~0.14)
    candidata_sobreposicao_parcial = (50, 50, 150, 150)
    idx_com_limiar_alto = indice_melhor_iou(
        [candidata_sobreposicao_parcial], caixa_alvo, iou_minimo=0.5,
    )
    idx_com_limiar_baixo = indice_melhor_iou(
        [candidata_sobreposicao_parcial], caixa_alvo, iou_minimo=0.05,
    )
    assert idx_com_limiar_alto is None
    assert idx_com_limiar_baixo == 0


# --------------------------------------------------------------------------
# Testes de _caixa_absoluta_para_cxcywh_normalizado -- conversão de formato
# exigida pela API real do SAM 3 (add_geometric_prompt), confirmada lendo
# o código-fonte oficial (facebookresearch/sam3), não documentação de
# terceiros.
# --------------------------------------------------------------------------

from src.segmentation.sam_segment import _caixa_absoluta_para_cxcywh_normalizado


def test_conversao_caixa_para_cxcywh_normalizado():
    # imagem 200x100, caixa exatamente no centro, 40x20 px
    caixa = (80, 40, 120, 60)  # x0,y0,x1,y1
    resultado = _caixa_absoluta_para_cxcywh_normalizado(caixa, largura_img=200, altura_img=100)

    cx, cy, w, h = resultado
    assert cx == pytest.approx(0.5)   # (80+120)/2 / 200 = 0.5
    assert cy == pytest.approx(0.5)   # (40+60)/2 / 100 = 0.5
    assert w == pytest.approx(0.2)    # (120-80) / 200 = 0.2
    assert h == pytest.approx(0.2)    # (60-40) / 100 = 0.2


def test_conversao_caixa_no_canto_superior_esquerdo():
    caixa = (0, 0, 50, 50)
    cx, cy, w, h = _caixa_absoluta_para_cxcywh_normalizado(caixa, largura_img=100, altura_img=100)
    assert cx == pytest.approx(0.25)
    assert cy == pytest.approx(0.25)
    assert w == pytest.approx(0.5)
    assert h == pytest.approx(0.5)


def test_conversao_e_o_inverso_da_conversao_yolo_ja_usada_no_projeto():
    """Confirma que a conversão para o SAM 3 é consistente com a mesma
    lógica cx/cy/w/h normalizados já usada em todo o projeto (compose.py,
    extrair_crops_de_yolo.py) -- não é um formato novo e paralelo, é o
    mesmo raciocínio aplicado no sentido inverso (pixels -> normalizado,
    em vez de normalizado -> pixels)."""
    largura_img, altura_img = 1920, 1080
    x0, y0, x1, y1 = 100, 200, 180, 260  # 80x60 px

    cx, cy, w, h = _caixa_absoluta_para_cxcywh_normalizado((x0, y0, x1, y1), largura_img, altura_img)

    # reconstrução manual, mesma fórmula usada em ler_caixas_yolo (compose.py) e no
    # extrator YOLO, só que no sentido inverso
    bw_px = w * largura_img
    bh_px = h * altura_img
    x0_reconstruido = round(cx * largura_img - bw_px / 2)
    y0_reconstruido = round(cy * altura_img - bh_px / 2)
    assert x0_reconstruido == x0
    assert y0_reconstruido == y0

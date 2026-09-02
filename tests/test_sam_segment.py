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

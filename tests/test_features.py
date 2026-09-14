"""Testes do módulo de features de CPU do Estágio A."""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from src.attribution.features import (
    calcular_features_geometricas,
    ajustar_regressao_escala_posicao,
    caixas_reais_do_alvo,
    calcular_features_intrinsecas,
)


def _linha_manifesto(x0, y0, x1, y1, W, H, crop_w, crop_h, fator_reescala):
    return {
        "caixa_x0_px": x0, "caixa_y0_px": y0, "caixa_x1_px": x1, "caixa_y1_px": y1,
        "imagem_largura_px": W, "imagem_altura_px": H,
        "crop_largura_original_px": crop_w, "crop_altura_original_px": crop_h,
        "fator_reescala": fator_reescala,
    }


# --------------------------------------------------------------------------
# Geometria e transformação
# --------------------------------------------------------------------------

def test_posicao_normalizada_centro_da_imagem():
    linha = _linha_manifesto(x0=900, y0=500, x1=1020, y1=580, W=1920, H=1080, crop_w=60, crop_h=40, fator_reescala=4.0)
    f = calcular_features_geometricas(linha)
    assert f["pos_h"] == pytest.approx((900 + 1020) / 2 / 1920)
    assert f["pos_v"] == pytest.approx((500 + 580) / 2 / 1080)
    assert f["area_caixa_norm"] == pytest.approx((120 * 80) / (1920 * 1080))
    assert f["menor_lado_caixa_px"] == 80


def test_distorcao_aspect_zero_quando_proporcoes_iguais():
    # caixa 120x80 (1.5), crop 60x40 (1.5) -> sem deformação
    linha = _linha_manifesto(0, 0, 120, 80, 1920, 1080, crop_w=60, crop_h=40, fator_reescala=4.0)
    f = calcular_features_geometricas(linha)
    assert f["distorcao_aspect"] == pytest.approx(0.0)


def test_distorcao_aspect_tem_sinal():
    # caixa quadrada (1.0), crop alongado (3.0) -> crop é ESPREMIDO -> log(1/3) < 0
    linha = _linha_manifesto(0, 0, 100, 100, 1920, 1080, crop_w=300, crop_h=100, fator_reescala=1.0)
    f_espremido = calcular_features_geometricas(linha)
    assert f_espremido["distorcao_aspect"] < 0

    # caixa alongada (3.0), crop quadrado (1.0) -> crop é ESTICADO -> log(3) > 0
    linha2 = _linha_manifesto(0, 0, 300, 100, 1920, 1080, crop_w=100, crop_h=100, fator_reescala=1.0)
    f_esticado = calcular_features_geometricas(linha2)
    assert f_esticado["distorcao_aspect"] > 0
    assert f_esticado["distorcao_aspect"] == pytest.approx(-f_espremido["distorcao_aspect"])


def test_log_fator_reescala_zero_quando_escala_casada():
    linha = _linha_manifesto(0, 0, 100, 100, 1920, 1080, crop_w=100, crop_h=100, fator_reescala=1.0)
    f = calcular_features_geometricas(linha)
    assert f["log_fator_reescala"] == pytest.approx(0.0)
    assert f["upsample"] == 0


def test_upsample_quando_fator_maior_que_um():
    linha = _linha_manifesto(0, 0, 100, 100, 1920, 1080, crop_w=50, crop_h=50, fator_reescala=4.0)
    f = calcular_features_geometricas(linha)
    assert f["upsample"] == 1
    assert f["log_fator_reescala"] == pytest.approx(math.log(4.0))


# --------------------------------------------------------------------------
# Regressão de coerência escala x posição
# --------------------------------------------------------------------------

def test_regressao_recupera_relacao_linear_conhecida():
    """Dados sintéticos com relação exata log(area) = -8 + 3*pos_v --
    a regressão deve recuperar os coeficientes."""
    pos_v = [0.1, 0.3, 0.5, 0.7, 0.9]
    area_norm = [math.exp(-8 + 3 * p) for p in pos_v]
    reg = ajustar_regressao_escala_posicao(pos_v, area_norm)
    assert reg.a == pytest.approx(-8.0, abs=1e-6)
    assert reg.b == pytest.approx(3.0, abs=1e-6)


def test_residuo_zero_para_caixa_exatamente_na_relacao():
    pos_v = [0.1, 0.3, 0.5, 0.7, 0.9]
    area_norm = [math.exp(-8 + 3 * p) for p in pos_v]
    reg = ajustar_regressao_escala_posicao(pos_v, area_norm)
    assert reg.residuo(pos_v=0.5, area_norm=math.exp(-8 + 3 * 0.5)) == pytest.approx(0.0, abs=1e-6)


def test_residuo_positivo_para_caixa_maior_que_o_esperado():
    pos_v = [0.1, 0.3, 0.5, 0.7, 0.9]
    area_norm = [math.exp(-8 + 3 * p) for p in pos_v]
    reg = ajustar_regressao_escala_posicao(pos_v, area_norm)
    # área 10x maior que a esperada para pos_v=0.5 -> resíduo = log(10)
    assert reg.residuo(pos_v=0.5, area_norm=10 * math.exp(-8 + 3 * 0.5)) == pytest.approx(math.log(10), abs=1e-6)


def test_regressao_degenerada_nao_quebra():
    reg = ajustar_regressao_escala_posicao([0.5, 0.5, 0.5], [0.01, 0.02, 0.03])
    assert reg.b == 0.0  # sem variação em pos_v -> inclinação zero, não erro


def test_caixas_reais_do_alvo_le_labels_yolo(tmp_path):
    labels_dir = tmp_path / "labels"
    labels_dir.mkdir()
    (labels_dir / "a.txt").write_text("0 0.5 0.3 0.1 0.2\n0 0.2 0.8 0.05 0.05\n")
    (labels_dir / "b.txt").write_text("0 0.7 0.6 0.2 0.1\n")

    pos_v, area_norm = caixas_reais_do_alvo(labels_dir)
    assert pos_v == [0.3, 0.8, 0.6]
    assert area_norm == pytest.approx([0.02, 0.0025, 0.02])


# --------------------------------------------------------------------------
# Intrínsecas do crop -- SÓ sobre a máscara
# --------------------------------------------------------------------------

def _salvar_rgba(caminho: Path, rgb: np.ndarray, alpha: np.ndarray):
    rgba = np.dstack([rgb, alpha]).astype(np.uint8)
    Image.fromarray(rgba, mode="RGBA").save(caminho)


def test_cobertura_mascara_calculada_do_alpha(tmp_path):
    rgb = np.full((10, 10, 3), 128, dtype=np.uint8)
    alpha = np.zeros((10, 10), dtype=np.uint8)
    alpha[:, :5] = 255  # metade esquerda opaca
    caminho = tmp_path / "crop.png"
    _salvar_rgba(caminho, rgb, alpha)

    f = calcular_features_intrinsecas(caminho)
    assert f["cobertura_mascara"] == pytest.approx(0.5)


def test_contraste_zero_para_crop_uniforme(tmp_path):
    rgb = np.full((20, 20, 3), 100, dtype=np.uint8)
    alpha = np.full((20, 20), 255, dtype=np.uint8)
    caminho = tmp_path / "crop.png"
    _salvar_rgba(caminho, rgb, alpha)

    f = calcular_features_intrinsecas(caminho)
    assert f["contraste"] == pytest.approx(0.0)
    assert f["nitidez"] == pytest.approx(0.0)
    assert f["brilho_medio"] == pytest.approx(100.0)


def test_nitidez_maior_para_padrao_xadrez_que_para_uniforme(tmp_path):
    """Xadrez (alta frequência) deve ter nitidez muito maior que um crop
    uniforme -- confirma que a medida responde a textura."""
    xadrez = np.indices((20, 20)).sum(axis=0) % 2 * 255
    rgb_xadrez = np.stack([xadrez] * 3, axis=-1).astype(np.uint8)
    alpha = np.full((20, 20), 255, dtype=np.uint8)
    caminho_xadrez = tmp_path / "xadrez.png"
    _salvar_rgba(caminho_xadrez, rgb_xadrez, alpha)

    rgb_uniforme = np.full((20, 20, 3), 128, dtype=np.uint8)
    caminho_uniforme = tmp_path / "uniforme.png"
    _salvar_rgba(caminho_uniforme, rgb_uniforme, alpha)

    f_x = calcular_features_intrinsecas(caminho_xadrez)
    f_u = calcular_features_intrinsecas(caminho_uniforme)
    assert f_x["nitidez"] > f_u["nitidez"]
    assert f_x["nitidez"] > 1000  # xadrez 0/255 gera Laplaciano enorme


def test_fundo_transparente_nao_contamina_medidas(tmp_path):
    """Crop com objeto uniforme + fundo transparente PRETO: se o fundo
    fosse contado, o contraste seria enorme (128 vs 0). Medindo só na
    máscara, o contraste deve ser zero."""
    rgb = np.zeros((20, 20, 3), dtype=np.uint8)
    rgb[5:15, 5:15, :] = 128  # objeto uniforme no centro
    alpha = np.zeros((20, 20), dtype=np.uint8)
    alpha[5:15, 5:15] = 255   # só o objeto é opaco
    caminho = tmp_path / "crop.png"
    _salvar_rgba(caminho, rgb, alpha)

    f = calcular_features_intrinsecas(caminho)
    assert f["contraste"] == pytest.approx(0.0)  # fundo preto NÃO entrou
    assert f["nitidez"] == pytest.approx(0.0)    # nem a aresta objeto/fundo
    assert f["brilho_medio"] == pytest.approx(128.0)

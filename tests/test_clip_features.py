"""Testes da matemática das features CLIP (CPU)."""
from __future__ import annotations

import numpy as np
import pytest

from src.attribution.clip_features import normalizar_l2, centroide_normalizado, dist_clip_alvo, novidade_pool


def test_normalizar_l2_da_norma_um():
    e = np.array([[3.0, 4.0], [0.0, 0.0], [1.0, 0.0]])
    n = normalizar_l2(e)
    assert np.allclose(np.linalg.norm(n[0]), 1.0)
    assert np.allclose(n[1], [0.0, 0.0])   # vetor nulo não vira NaN
    assert np.allclose(n[2], [1.0, 0.0])


def test_dist_clip_alvo_zero_para_crop_igual_ao_centroide():
    alvo = np.array([[1.0, 0.0], [1.0, 0.0]])
    crops = np.array([[2.0, 0.0], [0.0, 1.0], [-1.0, 0.0]])
    d = dist_clip_alvo(crops, alvo)
    assert d[0] == pytest.approx(0.0)   # mesma direção -> distância 0
    assert d[1] == pytest.approx(1.0)   # ortogonal -> 1
    assert d[2] == pytest.approx(2.0)   # oposto -> 2


def test_centroide_e_media_das_direcoes():
    alvo = np.array([[1.0, 0.0], [0.0, 1.0]])
    c = centroide_normalizado(alvo)
    assert np.allclose(c, [1 / np.sqrt(2), 1 / np.sqrt(2)])


def test_novidade_exclui_o_proprio_crop():
    """Dois crops idênticos + um distinto: os idênticos são vizinhos um do
    outro (novidade 0); o distinto tem novidade > 0. Se o próprio crop NÃO
    fosse excluído, TODOS teriam novidade 0."""
    pool = np.array([[1.0, 0.0], [1.0, 0.0], [0.0, 1.0]])
    nov, viz = novidade_pool(pool)
    assert nov[0] == pytest.approx(0.0) and viz[0] == 1
    assert nov[1] == pytest.approx(0.0) and viz[1] == 0
    assert nov[2] == pytest.approx(1.0)
    assert viz[2] in (0, 1)


def test_novidade_em_blocos_igual_a_sem_blocos():
    rng = np.random.default_rng(0)
    pool = rng.normal(size=(50, 8))
    nov_a, viz_a = novidade_pool(pool, tamanho_bloco=7)     # blocos não múltiplos de n
    nov_b, viz_b = novidade_pool(pool, tamanho_bloco=1000)  # um bloco só
    assert np.allclose(nov_a, nov_b, atol=1e-6)
    assert (viz_a == viz_b).all()


def test_novidade_nunca_negativa_e_no_maximo_dois():
    rng = np.random.default_rng(1)
    pool = rng.normal(size=(30, 5))
    nov, _ = novidade_pool(pool)
    assert (nov >= -1e-6).all() and (nov <= 2.0 + 1e-6).all()

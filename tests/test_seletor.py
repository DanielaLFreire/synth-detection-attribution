"""Testes do seletor de crop por célula (Fase 3, adendo 2)."""
from __future__ import annotations

import random
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from src.compose.compose import CaixaAlvo as CaixaCompositor, compor_dataset
from src.factorial import CropElegivel, construir_seletor_celula, CaixaPermitidaSemCrop, FONTES_ELEGIVEIS


def _pool(tmp_path, mediana=50.0):
    """Por fonte: crops de área 100, 400, 1600, 6400 (lados 10, 20, 40, 80),
    nos dois níveis de contraste. Arquivos RGBA reais, para o compositor."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    pool, caminhos = [], {}
    for f in FONTES_ELEGIVEIS:
        for lado in (10, 20, 40, 80):
            for nivel, ctr in (("alto", mediana + 10), ("baixo", mediana - 10)):
                nome = f"{f}_{lado}_{nivel}.png"
                p = tmp_path / nome
                Image.fromarray(np.full((lado, lado, 4), 200, dtype=np.uint8), "RGBA").save(p)
                pool.append(CropElegivel(nome, f, float(lado * lado), ctr))
                caminhos[nome] = p
    return pool, caminhos


def _caixa(box_index, lado):
    return CaixaCompositor(box_index=box_index, x0=0, y0=0, x1=lado, y1=lado)


def test_caixa_nao_permitida_fica_real(tmp_path):
    pool, caminhos = _pool(tmp_path)
    sel = construir_seletor_celula(pool, caminhos, 50.0, "casada", "alto", caixas_permitidas={("img", 0)}, minimo_por_fonte=1)
    assert sel("img", _caixa(1, 40), random.Random(0)) is None   # box 1 não permitida
    assert sel("outra", _caixa(0, 40), random.Random(0)) is None # outra imagem


def test_crop_escolhido_respeita_nivel_de_escala_e_contraste(tmp_path):
    pool, caminhos = _pool(tmp_path)
    caixa = _caixa(0, 40)  # área 1600 -> casada: crops de área em [800, 3200] -> só lado 40
    sel = construir_seletor_celula(pool, caminhos, 50.0, "casada", "alto", {("img", 0)}, minimo_por_fonte=1)
    for s in range(20):
        fonte, caminho = sel("img", caixa, random.Random(s))
        assert caminho.name.endswith("_40_alto.png"), caminho.name
        assert fonte in FONTES_ELEGIVEIS
    sel_red = construir_seletor_celula(pool, caminhos, 50.0, "reduzida", "baixo", {("img", 0)}, minimo_por_fonte=1)
    for s in range(20):
        _, caminho = sel_red("img", caixa, random.Random(s))
        assert caminho.name.endswith("_80_baixo.png")  # reduzida: área > 3200 -> só lado 80


def test_fonte_balanceada_em_expectativa(tmp_path):
    pool, caminhos = _pool(tmp_path)
    sel = construir_seletor_celula(pool, caminhos, 50.0, "casada", "alto", {("img", 0)}, minimo_por_fonte=1)
    rng = random.Random(123)
    contagem = {f: 0 for f in FONTES_ELEGIVEIS}
    for _ in range(3000):
        fonte, _ = sel("img", _caixa(0, 40), rng)
        contagem[fonte] += 1
    for f in FONTES_ELEGIVEIS:
        assert 0.28 < contagem[f] / 3000 < 0.39, contagem


def test_erro_claro_se_caixa_permitida_nao_tem_crops(tmp_path):
    pool, caminhos = _pool(tmp_path)
    # caixa de lado 5 (área 25): casada exige área em [12.5, 50] -> não existe (mínimo 100)
    sel = construir_seletor_celula(pool, caminhos, 50.0, "casada", "alto", {("img", 0)}, minimo_por_fonte=1)
    with pytest.raises(CaixaPermitidaSemCrop):
        sel("img", _caixa(0, 5), random.Random(0))


def test_determinismo_dado_o_rng(tmp_path):
    pool, caminhos = _pool(tmp_path)
    sel = construir_seletor_celula(pool, caminhos, 50.0, "reduzida", "alto", {("img", 0)}, minimo_por_fonte=1)
    a = sel("img", _caixa(0, 20), random.Random(7))
    b = sel("img", _caixa(0, 20), random.Random(7))
    assert a == b


def test_compositor_com_seletor_deixa_caixas_reais_e_registra(tmp_path):
    """Integração: imagem com 2 caixas, só uma permitida -> 1 colagem no
    manifesto, 1 caixa mantida real no metadata, label com as 2 caixas."""
    import json
    pool, caminhos = _pool(tmp_path / "pool")
    imgs = tmp_path / "images"; labels = tmp_path / "labels"; imgs.mkdir(); labels.mkdir()
    Image.fromarray(np.full((200, 200, 3), 30, dtype=np.uint8)).save(imgs / "img.png")
    # duas caixas de lado 40 (0.2 normalizado): centros 0.2 e 0.7
    (labels / "img.txt").write_text("0 0.2 0.2 0.2 0.2\n0 0.7 0.7 0.2 0.2\n")
    sel = construir_seletor_celula(pool, caminhos, 50.0, "casada", "alto", {("img", 0)}, minimo_por_fonte=1)
    n = compor_dataset(
        imagens_alvo_dir=imgs, labels_alvo_dir=labels, pool_crops=[], saida_imagens_dir=tmp_path / "out_i",
        saida_labels_dir=tmp_path / "out_l", manifesto_csv=tmp_path / "m.csv", manifesto_metadata_json=tmp_path / "m.json",
        split="train", n_variacoes=2, seed=1, permitir_split_treino=True, seletor_de_crop=sel,
    )
    assert n == 2  # 1 caixa colada x 2 variações
    meta = json.loads((tmp_path / "m.json").read_text())
    assert meta["config"]["n_caixas_mantidas_reais"] == 2  # 1 caixa real x 2 variações
    assert meta["config"]["usa_seletor_de_crop"] is True
    label = (tmp_path / "out_l" / "img_v00.txt").read_text().strip().splitlines()
    assert len(label) == 2  # a caixa real continua anotada

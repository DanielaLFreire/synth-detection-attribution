"""Testes da viabilidade das células da Fase 3."""
from __future__ import annotations

import pytest

from src.factorial import (
    CropElegivel, CaixaAlvo, nivel_escala, nivel_contraste, contar_elegiveis,
    verificar_viabilidade, comparar_geometria, FONTES_ELEGIVEIS,
)


def test_nivel_escala_fronteiras_inclusivas_na_casada():
    assert nivel_escala(0.5) == "casada"
    assert nivel_escala(2.0) == "casada"
    assert nivel_escala(1.0) == "casada"
    assert nivel_escala(0.499) == "reduzida"
    assert nivel_escala(2.001) == "ampliada"
    assert nivel_escala(0.01) == "reduzida"   # crop 100x maior que a caixa
    assert nivel_escala(50.0) == "ampliada"   # crop 50x menor que a caixa


def test_nivel_contraste_mediana_vai_para_baixo():
    assert nivel_contraste(41.0, mediana=40.0) == "alto"
    assert nivel_contraste(40.0, mediana=40.0) == "baixo"


def test_contar_elegiveis_coerente_com_nivel_escala():
    """Contagem por bisect deve bater com a classificação crop a crop."""
    areas = sorted([10, 50, 100, 200, 400, 800, 1600, 3200])
    A = 400.0
    for nivel in ("casada", "reduzida", "ampliada"):
        esperado = sum(1 for a in areas if nivel_escala(A / a) == nivel)
        assert contar_elegiveis(A, areas, nivel) == esperado, nivel
    # e as três contagens cobrem todo o pool
    assert sum(contar_elegiveis(A, areas, n) for n in ("casada", "reduzida", "ampliada")) == len(areas)


def _pool_completo(mediana=50.0):
    """Para cada fonte, crops de área 10, 100, 1000, 10000 nos dois níveis de contraste."""
    pool = []
    for f in FONTES_ELEGIVEIS:
        for area in (10, 100, 1000, 10000):
            pool.append(CropElegivel(f"{f}_{area}_alto", f, area, mediana + 10))
            pool.append(CropElegivel(f"{f}_{area}_baixo", f, area, mediana - 10))
    return pool


def test_caixa_viavel_em_todas_as_celulas():
    # caixa de área 300: casada <- 1000? não (fator 0.3). casada <- 100 (fator 3)? não.
    # use área 500: casada <- 1000 (fator 0.5, inclusivo); reduzida <- 10000; ampliada <- 100, 10.
    caixa = CaixaAlvo("img", 0, 500.0)
    r = verificar_viabilidade([caixa], _pool_completo(), mediana_contraste=50.0)
    assert len(r.caixas_viaveis) == 1 and not r.caixas_excluidas
    for cel, n in r.viaveis_por_celula.items():
        assert n == 1, cel


def test_caixa_inviavel_em_uma_celula_e_excluida_de_todas():
    """Caixa gigante: não existe crop maior que 2A em nenhuma fonte -> 'reduzida'
    inviável -> excluída do fatorial inteiro, mesmo sendo viável nas outras."""
    caixa = CaixaAlvo("img", 0, 1e6)
    r = verificar_viabilidade([caixa], _pool_completo(), mediana_contraste=50.0)
    assert not r.caixas_viaveis and len(r.caixas_excluidas) == 1
    assert r.viaveis_por_celula["reduzida__alto"] == 0
    assert r.viaveis_por_celula["ampliada__alto"] == 1  # viável aqui, mas não basta


def test_falta_em_uma_fonte_basta_para_inviabilizar():
    pool = [c for c in _pool_completo() if not (c.fonte == "SeaShips" and c.area_px == 10000)]
    caixa = CaixaAlvo("img", 0, 500.0)
    r = verificar_viabilidade([caixa], pool, mediana_contraste=50.0)
    # reduzida exige area_crop > 1000: só o 10000 servia; SeaShips ficou sem -> inviável
    assert not r.caixas_viaveis


def test_minimo_por_fonte_maior_que_um():
    caixa = CaixaAlvo("img", 0, 500.0)
    r1 = verificar_viabilidade([caixa], _pool_completo(), mediana_contraste=50.0, minimo_por_fonte=1)
    r2 = verificar_viabilidade([caixa], _pool_completo(), mediana_contraste=50.0, minimo_por_fonte=2)
    assert len(r1.caixas_viaveis) == 1
    assert len(r2.caixas_viaveis) == 0  # 'reduzida' só tem 1 crop (10000) por fonte/contraste


def test_mediana_calculada_do_pool_elegivel_ignora_fontes_fora():
    pool = _pool_completo(mediana=50.0) + [CropElegivel("ina", "InaTechShips", 100, 1e6)]
    r = verificar_viabilidade([CaixaAlvo("img", 0, 500.0)], pool)
    assert r.mediana_contraste == 50.0  # o 1e6 do InaTechShips não entrou


def test_comparar_geometria_detecta_exclusao_sistematica():
    viaveis = [CaixaAlvo("a", i, 100.0) for i in range(5)]
    excluidas = [CaixaAlvo("b", i, 5000.0) for i in range(5)]
    g = comparar_geometria(viaveis, excluidas)
    assert g["viaveis"]["fracao_small"] == 1.0
    assert g["excluidas"]["fracao_small"] == 0.0


def test_niveis_escala_restritos_ignoram_ampliada():
    """Caixa small (área 500): 'ampliada' exige crop < 250 px², inexistente
    no pool (mínimo 10? não -- use pool sem crops pequenos). Com só
    casada/reduzida a caixa vira viável."""
    pool = [c for c in _pool_completo() if c.area_px >= 100]  # sem crops de área 10
    caixa = CaixaAlvo("img", 0, 150.0)  # ampliada exigiria area_crop < 75: não há
    r3 = verificar_viabilidade([caixa], pool, mediana_contraste=50.0)
    r2 = verificar_viabilidade([caixa], pool, mediana_contraste=50.0, niveis_escala=["casada", "reduzida"])
    assert not r3.caixas_viaveis
    assert len(r2.caixas_viaveis) == 1
    assert set(r2.viaveis_por_celula) == {"casada__alto", "casada__baixo", "reduzida__alto", "reduzida__baixo"}

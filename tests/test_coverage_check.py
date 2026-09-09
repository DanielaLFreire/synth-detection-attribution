"""Testes da tarefa 0.3: simulação de compatibilidade de escala para
verificar cobertura do reservatório por fonte."""
from __future__ import annotations

from src.profiling import simular_compatibilidade_escala


def test_fonte_com_tamanho_parecido_ao_destino_produz_maioria_casada():
    """Crops e destinos de tamanho semelhante -> fator_reescala perto de
    1 na maioria das amostras -> maioria cai na faixa 'casada'."""
    tamanhos_origem = [(50, 50)] * 20
    tamanhos_destino = [(45, 55), (55, 45), (48, 52)] * 10

    resultado = simular_compatibilidade_escala(
        fonte="FonteParecida", tamanhos_origem=tamanhos_origem,
        tamanhos_destino=tamanhos_destino, n_amostras=1000,
    )
    assert resultado.pct_casada > 90


def test_fonte_com_crops_muito_maiores_que_destino_produz_maioria_downscale():
    """Reproduz o risco real identificado com o InaTechShips: crops muito
    maiores que o destino (mediana 358px vs. destino tipicamente <100px)
    devem produzir fator_reescala << 1 na maioria das amostras --
    'descasada_downscale', não 'casada'."""
    tamanhos_origem_grandes = [(400, 350)] * 20   # perfil estilo InaTechShips
    tamanhos_destino_pequenos = [(30, 25), (25, 30), (40, 35)] * 10  # perfil estilo CITRA

    resultado = simular_compatibilidade_escala(
        fonte="InaTechShips", tamanhos_origem=tamanhos_origem_grandes,
        tamanhos_destino=tamanhos_destino_pequenos, n_amostras=1000,
    )
    assert resultado.pct_descasada_downscale > 90
    assert resultado.pct_casada < 10  # confirma a incapacidade de cobrir a célula "casada"


def test_fonte_com_crops_muito_menores_que_destino_produz_maioria_upscale():
    tamanhos_origem_pequenos = [(10, 10)] * 20
    tamanhos_destino_grandes = [(200, 200)] * 10

    resultado = simular_compatibilidade_escala(
        fonte="FontePequena", tamanhos_origem=tamanhos_origem_pequenos,
        tamanhos_destino=tamanhos_destino_grandes, n_amostras=1000,
    )
    assert resultado.pct_descasada_upscale > 90


def test_reservatorio_vazio_nao_quebra():
    resultado = simular_compatibilidade_escala(
        fonte="FonteVazia", tamanhos_origem=[], tamanhos_destino=[(50, 50)], n_amostras=100,
    )
    assert resultado.n_amostras == 0


def test_simulacao_e_deterministica_com_mesma_seed():
    tamanhos_origem = [(30, 40), (60, 20), (15, 90)]
    tamanhos_destino = [(50, 50), (20, 20)]

    r1 = simular_compatibilidade_escala(
        fonte="F", tamanhos_origem=tamanhos_origem, tamanhos_destino=tamanhos_destino,
        n_amostras=500, seed=123,
    )
    r2 = simular_compatibilidade_escala(
        fonte="F", tamanhos_origem=tamanhos_origem, tamanhos_destino=tamanhos_destino,
        n_amostras=500, seed=123,
    )
    assert r1.pct_casada == r2.pct_casada
    assert r1.pct_descasada_downscale == r2.pct_descasada_downscale
    assert r1.pct_descasada_upscale == r2.pct_descasada_upscale

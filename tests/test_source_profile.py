"""Testes da tarefa 0.2: perfilamento de fontes de crop e tabela de
decisão de min_dim_px."""
from __future__ import annotations

import csv
from pathlib import Path

from src.profiling import perfilar_fonte, tabela_decisao_min_dim_px


def _criar_manifesto_sintetico(caminho: Path, dimensoes: list[tuple[int, int]]):
    """dimensoes: lista de (largura_px, altura_px) de crops extraídos com sucesso."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["extraido", "largura_px", "altura_px"])
        for largura, altura in dimensoes:
            writer.writerow(["True", largura, altura])
        writer.writerow(["False", 0, 0])  # linha de falha, deve ser ignorada


def test_perfilar_fonte_calcula_estatisticas_do_menor_lado(tmp_path):
    caminho = tmp_path / "manifesto.csv"
    _criar_manifesto_sintetico(caminho, [(10, 20), (30, 15), (50, 60), (5, 100)])

    perfil = perfilar_fonte(caminho, fonte="FonteTeste")

    assert perfil["fonte"] == "FonteTeste"
    assert perfil["n_crops"] == 4  # a linha extraido=False não conta
    # menores lados: min(10,20)=10, min(30,15)=15, min(50,60)=50, min(5,100)=5
    assert perfil["menor_lado_min"] == 5
    assert perfil["menor_lado_max"] == 50


def test_perfilar_fonte_manifesto_vazio_nao_quebra(tmp_path):
    caminho = tmp_path / "manifesto_vazio.csv"
    _criar_manifesto_sintetico(caminho, [])

    perfil = perfilar_fonte(caminho, fonte="FonteVazia")
    assert perfil["n_crops"] == 0


def test_tabela_decisao_conta_corretamente_por_limiar(tmp_path):
    caminho = tmp_path / "manifesto.csv"
    # menores lados: 5, 15, 25, 35
    _criar_manifesto_sintetico(caminho, [(5, 100), (15, 100), (25, 100), (35, 100)])
    perfil = perfilar_fonte(caminho, fonte="FonteX")

    tabela = tabela_decisao_min_dim_px([perfil], candidatos=[10, 20, 30])

    assert len(tabela) == 1
    linha = tabela[0]
    assert linha["fonte"] == "FonteX"
    assert linha["n_crops_total"] == 4
    # limiar 10: mantém lados >=10 -> 15,25,35 = 3
    assert linha["mantidos_em_10px"] == 3
    # limiar 20: mantém >=20 -> 25,35 = 2
    assert linha["mantidos_em_20px"] == 2
    # limiar 30: mantém >=30 -> 35 = 1
    assert linha["mantidos_em_30px"] == 1
    assert linha["pct_mantidos_em_30px"] == 25.0


def test_tabela_decisao_ignora_fontes_vazias(tmp_path):
    caminho_vazio = tmp_path / "vazio.csv"
    caminho_com_dados = tmp_path / "com_dados.csv"
    _criar_manifesto_sintetico(caminho_vazio, [])
    _criar_manifesto_sintetico(caminho_com_dados, [(20, 20)])

    perfil_vazio = perfilar_fonte(caminho_vazio, fonte="Vazia")
    perfil_com_dados = perfilar_fonte(caminho_com_dados, fonte="ComDados")

    tabela = tabela_decisao_min_dim_px([perfil_vazio, perfil_com_dados], candidatos=[10])
    assert len(tabela) == 1
    assert tabela[0]["fonte"] == "ComDados"


def test_tabela_decisao_compara_multiplas_fontes_com_perfis_diferentes(tmp_path):
    """Simula o caso real: uma fonte com objetos maiores (SeaShips-like) e
    outra com muitos objetos pequenos (ABOShips-like) -- confirma que a
    tabela revela o trade-off, não escolhe um número sozinha."""
    caminho_grande = tmp_path / "fonte_objetos_grandes.csv"
    caminho_pequena = tmp_path / "fonte_objetos_pequenos.csv"
    _criar_manifesto_sintetico(caminho_grande, [(40, 40)] * 10)
    _criar_manifesto_sintetico(caminho_pequena, [(10, 10)] * 6 + [(40, 40)] * 4)

    perfil_grande = perfilar_fonte(caminho_grande, fonte="Grande")
    perfil_pequena = perfilar_fonte(caminho_pequena, fonte="Pequena")

    tabela = tabela_decisao_min_dim_px([perfil_grande, perfil_pequena], candidatos=[20])

    linha_grande = next(l for l in tabela if l["fonte"] == "Grande")
    linha_pequena = next(l for l in tabela if l["fonte"] == "Pequena")

    assert linha_grande["pct_mantidos_em_20px"] == 100.0  # nenhum descartado
    assert linha_pequena["pct_mantidos_em_20px"] == 40.0   # 4 de 10 sobrevivem


def test_perfilar_fonte_aceita_lista_de_multiplos_manifestos(tmp_path):
    """Caso do InaTechShips: extraído em três manifestos separados
    (train/val/test) que precisam ser combinados num único perfil."""
    caminho_train = tmp_path / "manifesto_train.csv"
    caminho_val = tmp_path / "manifesto_val.csv"
    caminho_test = tmp_path / "manifesto_test.csv"
    _criar_manifesto_sintetico(caminho_train, [(30, 30), (40, 40)])
    _criar_manifesto_sintetico(caminho_val, [(10, 10)])
    _criar_manifesto_sintetico(caminho_test, [(50, 50)])

    perfil = perfilar_fonte([caminho_train, caminho_val, caminho_test], fonte="InaTechShips")

    assert perfil["n_crops"] == 4  # 2 + 1 + 1, combinados
    assert perfil["menor_lado_min"] == 10
    assert perfil["menor_lado_max"] == 50

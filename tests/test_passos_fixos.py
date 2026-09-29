"""Fase 5, G1 (adendo 3 §4, §8): cada número do desenho lacrado,
verificado contra o código que o implementa."""
from __future__ import annotations

import pytest

from src.train import ProtocoloTreinoV2, ProtocoloInvalido, gerar_kwargs_treino, passos_de_warmup_reais
from src.train.passos_fixos import (
    BRACOS, COMPRIMENTO_LISTA, N_REAIS_TREINO, ORCAMENTOS, SEEDS,
    DesenhoInvalido, ExecucaoF5, composicao_braco, diferencas_de_kwargs,
    execucoes_portao_g2, kwargs_execucao, passos_por_epoca, planejar_execucoes,
)


# --- close_mosaic explícito no protocolo (§4.4, §8 G1) ---

def test_close_mosaic_padrao_e_10_e_vai_para_os_kwargs():
    """Padrão 10 = comportamento implícito do Ultralytics nas Fases 1-3:
    as configurações antigas permanecem idênticas."""
    p = ProtocoloTreinoV2(pesos_base="yolo11n.pt", epochs_total=150, epoca_checkpoint=150)
    assert p.close_mosaic == 10
    assert gerar_kwargs_treino(p, 2696, "controle", 42)["close_mosaic"] == 10


@pytest.mark.parametrize("valor", [-1, 151])
def test_close_mosaic_fora_do_intervalo_e_rejeitado(valor):
    with pytest.raises(ProtocoloInvalido, match="close_mosaic"):
        ProtocoloTreinoV2(pesos_base="yolo11n.pt", epochs_total=150, epoca_checkpoint=150, close_mosaic=valor)


# --- números do adendo ---

def test_passos_por_epoca_da_lista_fixa_e_337():
    assert passos_por_epoca(COMPRIMENTO_LISTA, 16) == 337


def test_passos_por_epoca_usa_teto_como_o_dataloader():
    assert passos_por_epoca(2696, 16) == 169
    assert passos_por_epoca(5288, 16) == 331  # células da Fase 3


def test_orcamentos_batem_com_o_adendo():
    assert (ORCAMENTOS["S1"].epocas, ORCAMENTOS["S1"].passos_totais, ORCAMENTOS["S1"].close_mosaic) == (30, 10110, 2)
    assert (ORCAMENTOS["S2"].epocas, ORCAMENTOS["S2"].passos_totais, ORCAMENTOS["S2"].close_mosaic) == (75, 25275, 5)


def test_s2_fica_a_menos_de_0_5_por_cento_do_controle_da_fase3():
    assert abs(ORCAMENTOS["S2"].passos_totais - 25350) / 25350 < 0.005


@pytest.mark.parametrize("braco,repeat,n_sint,p", [("C", 4, 0, 0.0), ("M25", 3, 1348, 0.25), ("M50", 2, 2696, 0.5)])
def test_composicao_dos_bracos(braco, repeat, n_sint, p):
    c = composicao_braco(braco)
    assert (c.repeat_real, c.n_sinteticas, c.n_total) == (repeat, n_sint, COMPRIMENTO_LISTA)
    assert c.fracao_sintetica == pytest.approx(p, abs=1e-12)


def test_braco_desconhecido_e_rejeitado():
    with pytest.raises(DesenhoInvalido):
        composicao_braco("M75")


# --- lista fechada de execuções (§4.5) ---

def test_plano_tem_30_execucoes_unicas_com_nomes_do_adendo():
    plano = planejar_execucoes()
    assert len(plano) == 30
    nomes = [e.nome for e in plano]
    assert len(set(nomes)) == 30
    assert "f5_S1_C_seed42" in nomes and "f5_S2_M50_seed31415" in nomes
    assert {e.orcamento for e in plano} == {"S1", "S2"}
    assert {e.braco for e in plano} == set(BRACOS)
    assert {e.seed for e in plano} == set(SEEDS) == {42, 123, 2024, 7, 31415}


def test_plano_mantem_os_tres_bracos_de_cada_seed_juntos():
    plano = planejar_execucoes()
    for i in range(0, 30, 3):
        bloco = plano[i:i + 3]
        assert len({(e.orcamento, e.seed) for e in bloco}) == 1
        assert [e.braco for e in bloco] == list(BRACOS)


def test_portao_g2_repete_f5_S1_C_seed42_em_pasta_propria():
    original, repeticao = execucoes_portao_g2()
    assert original in planejar_execucoes()
    assert repeticao not in planejar_execucoes()
    assert original.nome == "f5_S1_C_seed42"
    assert repeticao.nome == "f5_S1_C_g2rep_seed42"
    assert original.como_execucao().nome != repeticao.como_execucao().nome
    assert original.como_execucao().nome == original.nome
    assert repeticao.como_execucao().nome == repeticao.nome
    assert kwargs_execucao(original)["seed"] == kwargs_execucao(repeticao)["seed"] == 42


# --- isolamento do tratamento (§8 G1) ---

@pytest.mark.parametrize("orc", ["S1", "S2"])
@pytest.mark.parametrize("seed", SEEDS)
def test_dentro_do_orcamento_os_bracos_diferem_so_no_nome(orc, seed):
    """O arquivo de dados é passado à parte (data=...); nos kwargs, a única
    diferença admissível entre braços é o nome da execução."""
    k = {b: kwargs_execucao(ExecucaoF5(orc, b, seed)) for b in BRACOS}
    assert diferencas_de_kwargs(k["C"], k["M25"]) == {"name"}
    assert diferencas_de_kwargs(k["C"], k["M50"]) == {"name"}


def test_entre_orcamentos_mudam_so_epocas_checkpoint_close_mosaic_e_nome():
    a = kwargs_execucao(ExecucaoF5("S1", "M50", 42))
    b = kwargs_execucao(ExecucaoF5("S2", "M50", 42))
    assert diferencas_de_kwargs(a, b) == {"epochs", "patience", "_epoca_checkpoint_a_usar", "close_mosaic", "name"}


@pytest.mark.parametrize("execucao", planejar_execucoes())
def test_kwargs_de_cada_execucao(execucao):
    k = kwargs_execucao(execucao)
    o = ORCAMENTOS[execucao.orcamento]
    assert k["epochs"] == k["_epoca_checkpoint_a_usar"] == o.epocas
    assert k["close_mosaic"] == o.epocas // 15
    assert k["patience"] == o.epocas + 1
    assert k["batch"] == 16 and k["model"] == "yolo11n.pt" and k["seed"] == execucao.seed
    assert passos_de_warmup_reais(k["warmup_epochs"], COMPRIMENTO_LISTA, 16) == pytest.approx(500, rel=1e-9)
    assert k["name"] == execucao.nome

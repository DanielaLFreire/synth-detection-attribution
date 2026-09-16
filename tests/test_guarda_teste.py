from __future__ import annotations

import pytest

from src.evaluation import verificar_avaliacao_unica, registrar_avaliacao, AvaliacaoDeTesteJaRealizada


def test_primeira_avaliacao_passa_e_registra(tmp_path):
    m = tmp_path / "teste_avaliado.json"
    verificar_avaliacao_unica(m)  # não levanta
    r = registrar_avaliacao(m, {"commit": "abc", "n_modelos": 18})
    assert m.exists() and r["commit"] == "abc" and "avaliado_em_utc" in r


def test_segunda_avaliacao_e_recusada(tmp_path):
    m = tmp_path / "teste_avaliado.json"
    registrar_avaliacao(m, {"commit": "abc"})
    with pytest.raises(AvaliacaoDeTesteJaRealizada, match="já foi avaliado"):
        verificar_avaliacao_unica(m)

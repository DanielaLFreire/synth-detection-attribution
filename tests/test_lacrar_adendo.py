"""Testes das salvaguardas de lacração de adendo."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.lacrar_adendo import lacrar_adendo, _sha256


def _preparar(tmp_path: Path, texto_adendo: str):
    hashes = tmp_path / "hashes.json"
    hashes.write_text(json.dumps({"artefatos": {"x.json": {"sha256": "abc", "encontrado": True}}}), encoding="utf-8")
    original = tmp_path / "previsoes_fase0.md"
    original.write_text("previsoes originais", encoding="utf-8")
    adendo = tmp_path / "adendo.md"
    adendo.write_text(texto_adendo, encoding="utf-8")
    return hashes, original, adendo


def test_recusa_lacrar_com_decisao_pendente(tmp_path):
    hashes, original, adendo = _preparar(tmp_path, "n_variacoes = ___ DECISÃO PENDENTE")
    with pytest.raises(ValueError, match="pendente"):
        lacrar_adendo(adendo, hashes, original)


def test_lacra_e_preserva_entradas_existentes(tmp_path):
    hashes, original, adendo = _preparar(tmp_path, "adendo fechado, n_variacoes = 2")
    entrada = lacrar_adendo(adendo, hashes, original)
    registro = json.loads(hashes.read_text(encoding="utf-8"))
    assert registro["artefatos"]["x.json"]["sha256"] == "abc"          # intocado
    assert registro["adendos"]["adendo.md"]["sha256"] == _sha256(adendo)
    assert entrada["sha256_previsoes_fase0_md_no_momento"] == _sha256(original)


def test_recusa_relacrar_o_mesmo_adendo(tmp_path):
    hashes, original, adendo = _preparar(tmp_path, "adendo fechado")
    lacrar_adendo(adendo, hashes, original)
    with pytest.raises(ValueError, match="já está lacrado"):
        lacrar_adendo(adendo, hashes, original)


def test_hash_muda_se_o_adendo_mudar(tmp_path):
    hashes, original, adendo = _preparar(tmp_path, "versão 1")
    e1 = lacrar_adendo(adendo, hashes, original)
    adendo2 = tmp_path / "adendo2.md"; adendo2.write_text("versão 2", encoding="utf-8")
    e2 = lacrar_adendo(adendo2, hashes, original)
    assert e1["sha256"] != e2["sha256"]

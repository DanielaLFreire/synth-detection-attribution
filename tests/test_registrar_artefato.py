"""Fase 5, G1: registro do hash do manifesto em hashes.json sem tocar no resto."""
from __future__ import annotations

import hashlib
import json

import pytest

from scripts.registrar_artefato import registrar_artefato


def test_registra_sem_alterar_entradas_existentes(tmp_path):
    hashes = tmp_path / "hashes.json"
    original = {"artefatos": {"a.json": {"sha256": "x"}}, "adendos": {"ad.md": {"sha256": "y"}}}
    hashes.write_text(json.dumps(original), encoding="utf-8")
    art = tmp_path / "amostra.csv"
    art.write_text("ordem,celula\n0,c\n", encoding="utf-8")

    entrada = registrar_artefato(art, hashes)
    novo = json.loads(hashes.read_text(encoding="utf-8"))
    assert novo["adendos"] == original["adendos"]
    assert novo["artefatos"]["a.json"] == original["artefatos"]["a.json"]
    assert entrada["sha256"] == hashlib.sha256(art.read_bytes()).hexdigest()
    assert novo["artefatos"]["amostra.csv"]["sha256"] == entrada["sha256"]


def test_recusa_re_registro(tmp_path):
    hashes = tmp_path / "hashes.json"
    hashes.write_text("{}", encoding="utf-8")
    art = tmp_path / "amostra.csv"
    art.write_text("x", encoding="utf-8")
    registrar_artefato(art, hashes)
    with pytest.raises(ValueError, match="já está registrado"):
        registrar_artefato(art, hashes)


def test_arquivo_inexistente(tmp_path):
    with pytest.raises(FileNotFoundError):
        registrar_artefato(tmp_path / "nao_existe.csv", tmp_path / "hashes.json")

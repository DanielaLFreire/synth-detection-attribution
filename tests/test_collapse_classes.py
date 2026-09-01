"""Testes da tarefa -1.8: colapso de múltiplas classes (UA-DETRAC: bus,
car, truck, van) para classe única."""
from __future__ import annotations

from pathlib import Path

import pytest

from src.materialize import colapsar_para_classe_unica, ClasseOriginalInesperada


def test_colapso_reescreve_classe_preservando_geometria(tmp_path):
    origem = tmp_path / "labels_multi"
    destino = tmp_path / "labels_unica"
    origem.mkdir()

    (origem / "img1.txt").write_text(
        "1 0.5 0.5 0.1 0.1\n0 0.2 0.2 0.05 0.05\n3 0.7 0.3 0.2 0.1\n"
    )

    relatorio = colapsar_para_classe_unica(
        labels_origem_dir=origem, labels_destino_dir=destino,
        classes_originais_validas={"0", "1", "2", "3"},
    )

    conteudo = (destino / "img1.txt").read_text()
    linhas = [l for l in conteudo.splitlines() if l]
    assert len(linhas) == 3
    for linha in linhas:
        assert linha.startswith("0 ")  # classe destino aplicada a todas
    # geometria preservada exatamente
    assert "0 0.5 0.5 0.1 0.1" in linhas
    assert "0 0.7 0.3 0.2 0.1" in linhas

    assert relatorio.n_arquivos == 1
    assert relatorio.n_linhas == 3
    assert relatorio.contagem_por_classe_original == {"0": 1, "1": 1, "2": 0, "3": 1}


def test_colapso_detecta_classe_fora_do_conjunto_declarado(tmp_path):
    origem = tmp_path / "labels_multi"
    destino = tmp_path / "labels_unica"
    origem.mkdir()
    (origem / "img1.txt").write_text("7 0.5 0.5 0.1 0.1\n")  # classe 7 não declarada

    with pytest.raises(ClasseOriginalInesperada, match="'7'"):
        colapsar_para_classe_unica(
            labels_origem_dir=origem, labels_destino_dir=destino,
            classes_originais_validas={"0", "1", "2", "3"},
        )


def test_colapso_processa_multiplos_arquivos(tmp_path):
    origem = tmp_path / "labels_multi"
    destino = tmp_path / "labels_unica"
    origem.mkdir()
    (origem / "img1.txt").write_text("0 0.1 0.1 0.1 0.1\n")
    (origem / "img2.txt").write_text("2 0.2 0.2 0.1 0.1\n1 0.3 0.3 0.1 0.1\n")

    relatorio = colapsar_para_classe_unica(
        labels_origem_dir=origem, labels_destino_dir=destino,
        classes_originais_validas={"0", "1", "2", "3"},
    )
    assert relatorio.n_arquivos == 2
    assert relatorio.n_linhas == 3
    assert (destino / "img1.txt").exists()
    assert (destino / "img2.txt").exists()

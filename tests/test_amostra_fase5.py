"""Fase 5, G1 (adendo 3 §4.3): amostra estratificada, aninhada e determinística."""
from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from src.factorial.amostra_fase5 import (
    CELULAS_FASE3, AmostraInvalida, achatar, amostrar_por_celula, decompor_nome,
    escrever_manifesto, ler_manifesto, resolver_manifesto, subconjunto_aninhado,
)


def _celulas(tmp: Path, n: int = 2592) -> dict[str, Path]:
    pastas = {}
    for c in CELULAS_FASE3:
        pasta = tmp / c / "images"
        pasta.mkdir(parents=True)
        for i in range(n // 2):
            for k in (0, 1):
                (pasta / f"img{i:05d}_v{k}.png").write_bytes(f"{c}-{i}-{k}".encode())
        pastas[c] = pasta
    return pastas


def test_tamanhos_do_adendo(tmp_path):
    a = amostrar_por_celula(_celulas(tmp_path))
    m25 = subconjunto_aninhado(a)
    assert all(len(v) == 674 for v in a.values()) and len(achatar(a)) == 2696
    assert all(len(v) == 337 for v in m25.values()) and len(achatar(m25)) == 1348


def test_sem_reposicao(tmp_path):
    a = amostrar_por_celula(_celulas(tmp_path))
    for lista in a.values():
        assert len(set(lista)) == len(lista)


def test_m25_aninhado_em_m50(tmp_path):
    a = amostrar_por_celula(_celulas(tmp_path))
    m25 = subconjunto_aninhado(a)
    assert set(achatar(m25)) <= set(achatar(a))
    for c in CELULAS_FASE3:
        assert m25[c] == a[c][:337]


def test_deterministica_e_independente_da_pasta(tmp_path):
    a1 = amostrar_por_celula(_celulas(tmp_path / "x"))
    a2 = amostrar_por_celula(_celulas(tmp_path / "y"))
    for c in CELULAS_FASE3:
        assert [p.name for p in a1[c]] == [p.name for p in a2[c]]


def test_semente_diferente_da_amostra_diferente(tmp_path):
    pastas = _celulas(tmp_path)
    a1 = amostrar_por_celula(pastas, semente=20260928)
    a2 = amostrar_por_celula(pastas, semente=1)
    assert [p.name for p in a1["casada__alto"]] != [p.name for p in a2["casada__alto"]]


def test_exige_2592_por_celula(tmp_path):
    with pytest.raises(AmostraInvalida, match="esperado 2592"):
        amostrar_por_celula(_celulas(tmp_path, n=2594))


def test_exige_as_quatro_celulas(tmp_path):
    pastas = _celulas(tmp_path)
    del pastas["reduzida__baixo"]
    with pytest.raises(AmostraInvalida, match="ausentes"):
        amostrar_por_celula(pastas)


def test_decompor_nome():
    assert decompor_nome("abc_v12_v1.png") == ("abc_v12", 1)
    with pytest.raises(AmostraInvalida):
        decompor_nome("sem_variacao.png")


def test_manifesto_portavel_e_hash_estavel(tmp_path):
    """Mesma amostra em duas raízes diferentes -> manifestos com bytes
    idênticos (sem caminho absoluto; hash registrável)."""
    m1, m2 = tmp_path / "m1.csv", tmp_path / "m2.csv"
    escrever_manifesto(amostrar_por_celula(_celulas(tmp_path / "x")), m1)
    escrever_manifesto(amostrar_por_celula(_celulas(tmp_path / "y")), m2)
    assert hashlib.sha256(m1.read_bytes()).hexdigest() == hashlib.sha256(m2.read_bytes()).hexdigest()
    assert str(tmp_path) not in m1.read_text(encoding="utf-8")


def test_manifesto_ida_e_volta(tmp_path):
    pastas = _celulas(tmp_path)
    a = amostrar_por_celula(pastas)
    m = tmp_path / "m.csv"
    assert escrever_manifesto(a, m) == 2696
    linhas = ler_manifesto(m)
    assert sum(l.em_m25 for l in linhas) == 1348
    assert resolver_manifesto(m, pastas) == achatar(a)
    assert resolver_manifesto(m, pastas, somente_m25=True) == achatar(subconjunto_aninhado(a))


def test_resolver_detecta_imagem_alterada(tmp_path):
    pastas = _celulas(tmp_path)
    a = amostrar_por_celula(pastas)
    m = tmp_path / "m.csv"
    escrever_manifesto(a, m)
    a["casada__baixo"][5].write_bytes(b"adulterada")
    with pytest.raises(AmostraInvalida, match="SHA-256"):
        resolver_manifesto(m, pastas)

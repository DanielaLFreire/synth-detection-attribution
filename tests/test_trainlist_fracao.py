"""Fase 5, G1 (adendo 3 §4.2): construtor e verificador de trainlist por fração."""
from __future__ import annotations

from pathlib import Path

import pytest

from src.train import TrainlistInvalida, construir_trainlist_fracao, verificar_trainlist_fracao
from src.train.passos_fixos import BRACOS, COMPRIMENTO_LISTA, N_REAIS_TREINO, composicao_braco


def _arquivos(pasta: Path, n: int, prefixo: str) -> list[Path]:
    pasta.mkdir(parents=True, exist_ok=True)
    out = []
    for i in range(n):
        p = pasta / f"{prefixo}{i:05d}.png"
        p.write_bytes(b"x")
        out.append(p)
    return out


@pytest.fixture
def dados(tmp_path):
    reais = _arquivos(tmp_path / "real" / "images", N_REAIS_TREINO, "r")
    sint = _arquivos(tmp_path / "sint" / "images", 2696, "s")
    return tmp_path, reais, sint


@pytest.mark.parametrize("braco", BRACOS)
def test_tres_bracos_em_escala_real_passam_na_verificacao(dados, braco):
    tmp, reais, sint = dados
    comp = composicao_braco(braco)
    s = sint[: comp.n_sinteticas]
    txt = tmp / f"tl_{braco}.txt"
    c = construir_trainlist_fracao(reais, s, txt, comp.repeat_real)
    v = verificar_trainlist_fracao(txt, reais, s, comp.repeat_real, COMPRIMENTO_LISTA)
    assert c.n_total == v.n_total == COMPRIMENTO_LISTA
    assert v.n_sintetico / v.n_total == pytest.approx({"C": 0.0, "M25": 0.25, "M50": 0.5}[braco])


def test_verificador_detecta_linha_a_mais(dados):
    tmp, reais, sint = dados
    txt = tmp / "tl.txt"
    construir_trainlist_fracao(reais, sint, txt, 2)
    with open(txt, "a", encoding="utf-8") as f:
        f.write(str(reais[0]) + "\n")
    with pytest.raises(TrainlistInvalida, match="Comprimento"):
        verificar_trainlist_fracao(txt, reais, sint, 2, COMPRIMENTO_LISTA)


def test_verificador_detecta_peso_desigual_com_comprimento_certo(dados):
    tmp, reais, sint = dados
    txt = tmp / "tl.txt"
    construir_trainlist_fracao(reais, sint, txt, 2)
    linhas = txt.read_text(encoding="utf-8").splitlines()
    linhas[0] = str(reais[1])  # troca uma ocorrência de reais[0] por reais[1]
    txt.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    with pytest.raises(TrainlistInvalida, match="peso"):
        verificar_trainlist_fracao(txt, reais, sint, 2, COMPRIMENTO_LISTA)


def test_verificador_detecta_caminho_estranho(dados):
    tmp, reais, sint = dados
    txt = tmp / "tl.txt"
    construir_trainlist_fracao(reais, sint, txt, 2)
    linhas = txt.read_text(encoding="utf-8").splitlines()
    linhas[-1] = str(tmp / "intruso.png")
    txt.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    with pytest.raises(TrainlistInvalida, match="fora das listas"):
        verificar_trainlist_fracao(txt, reais, sint, 2, COMPRIMENTO_LISTA)


def test_construtor_recusa_duplicatas_e_sobreposicao(tmp_path):
    reais = _arquivos(tmp_path / "r", 3, "r")
    sint = _arquivos(tmp_path / "s", 3, "s")
    with pytest.raises(TrainlistInvalida, match="reais"):
        construir_trainlist_fracao(reais + [reais[0]], sint, tmp_path / "a.txt", 1)
    with pytest.raises(TrainlistInvalida, match="sintéticas"):
        construir_trainlist_fracao(reais, sint + [sint[0]], tmp_path / "b.txt", 1)
    with pytest.raises(TrainlistInvalida, match="real e como sintético"):
        construir_trainlist_fracao(reais, [reais[0]], tmp_path / "c.txt", 1)
    with pytest.raises(TrainlistInvalida, match="repeat_real"):
        construir_trainlist_fracao(reais, sint, tmp_path / "d.txt", 0)

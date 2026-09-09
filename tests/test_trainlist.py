"""Testes da Fase 1: montagem de trainlist balanceado real/sintético e
do braço de controle real-sobreamostrado."""
from __future__ import annotations

from pathlib import Path

from PIL import Image

from src.train import construir_trainlist_balanceado, construir_trainlist_real_sobreamostrado


def _criar_imagens(pasta: Path, n: int, prefixo: str):
    pasta.mkdir(parents=True, exist_ok=True)
    for i in range(n):
        Image.new("RGB", (10, 10)).save(pasta / f"{prefixo}_{i:03d}.png")


def test_trainlist_balanceado_repete_real_e_mantem_sintetico_uma_vez(tmp_path):
    reais_dir = tmp_path / "reais"
    sint_dir = tmp_path / "sinteticas"
    _criar_imagens(reais_dir, n=4, prefixo="real")
    _criar_imagens(sint_dir, n=10, prefixo="sint")

    destino = tmp_path / "trainlist.txt"
    contagem = construir_trainlist_balanceado(reais_dir, sint_dir, destino, repeat_real=3)

    assert contagem.n_real == 12   # 4 reais x 3 repetições
    assert contagem.n_sintetico == 10
    assert contagem.n_total == 22

    linhas = destino.read_text().splitlines()
    assert len(linhas) == 22
    # as primeiras 12 linhas devem ser reais (4 arquivos x 3 repetições, na ordem)
    assert all("real" in l for l in linhas[:12])
    assert all("sint" in l for l in linhas[12:])


def test_trainlist_balanceado_proximo_de_50_50_com_repeat_real_13(tmp_path):
    """Reproduz a lógica real da Fase 1: 1348 imagens reais x 13 repetições
    deve ficar perto de 50/50 quando o sintético tem volume comparável
    (aqui simulado em escala menor, mesma proporção)."""
    reais_dir = tmp_path / "reais"
    sint_dir = tmp_path / "sinteticas"
    _criar_imagens(reais_dir, n=100, prefixo="real")     # equivalente proporcional a 1348
    _criar_imagens(sint_dir, n=1300, prefixo="sint")     # equivalente proporcional a 17524 (100*13)

    destino = tmp_path / "trainlist.txt"
    contagem = construir_trainlist_balanceado(reais_dir, sint_dir, destino, repeat_real=13)

    assert contagem.n_real == 1300
    assert contagem.n_sintetico == 1300
    assert abs(contagem.proporcao_real - 0.5) < 0.01


def test_trainlist_real_sobreamostrado_nao_inclui_sintetico(tmp_path):
    reais_dir = tmp_path / "reais"
    _criar_imagens(reais_dir, n=5, prefixo="real")

    destino = tmp_path / "trainlist_controle.txt"
    contagem = construir_trainlist_real_sobreamostrado(reais_dir, destino, repeat_real=13)

    assert contagem.n_real == 65   # 5 x 13
    assert contagem.n_sintetico == 0
    assert contagem.proporcao_real == 1.0

    linhas = destino.read_text().splitlines()
    assert len(linhas) == 65
    assert all("real" in l for l in linhas)


def test_trainlist_balanceado_com_pastas_vazias_nao_quebra(tmp_path):
    reais_dir = tmp_path / "reais"
    sint_dir = tmp_path / "sinteticas"
    reais_dir.mkdir()
    sint_dir.mkdir()

    destino = tmp_path / "trainlist.txt"
    contagem = construir_trainlist_balanceado(reais_dir, sint_dir, destino, repeat_real=13)
    assert contagem.n_total == 0
    assert contagem.proporcao_real == 0.0

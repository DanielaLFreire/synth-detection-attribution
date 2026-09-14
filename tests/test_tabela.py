"""Testes do montador da tabela de features do Estágio A."""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
from PIL import Image

from src.attribution import construir_tabela_features, construir_indice_crops


def _salvar_crop_rgba(caminho: Path, valor: int):
    rgb = np.full((20, 20, 3), valor, dtype=np.uint8)
    alpha = np.full((20, 20), 255, dtype=np.uint8)
    Image.fromarray(np.dstack([rgb, alpha]).astype(np.uint8), mode="RGBA").save(caminho)


def _escrever_alvo(caminho: Path, linhas: list[dict]):
    campos = ["imagem_id", "grupo_geometrico_id", "caixa_x0_px", "caixa_y0_px", "caixa_x1_px", "caixa_y1_px",
              "imagem_largura_px", "imagem_altura_px", "crop_largura_original_px", "crop_altura_original_px",
              "fator_reescala", "upsample", "fonte", "crop_path", "acerto_votacao"]
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(linhas)


def _preparar(tmp_path: Path):
    crops_dir = tmp_path / "crops"
    crops_dir.mkdir()
    _salvar_crop_rgba(crops_dir / "crop_a.png", 100)
    _salvar_crop_rgba(crops_dir / "crop_b.png", 200)

    labels_dir = tmp_path / "labels_reais"
    labels_dir.mkdir()
    (labels_dir / "r1.txt").write_text("0 0.5 0.3 0.1 0.1\n0 0.5 0.8 0.3 0.3\n")

    alvo = tmp_path / "alvo.csv"
    base = {"imagem_largura_px": 1920, "imagem_altura_px": 1080,
            "crop_largura_original_px": 60, "crop_altura_original_px": 40,
            "fator_reescala": 2.0, "upsample": "True", "fonte": "SMD", "acerto_votacao": 1}
    _escrever_alvo(alvo, [
        {**base, "imagem_id": "img1", "grupo_geometrico_id": "img1__0",
         "caixa_x0_px": 100, "caixa_y0_px": 100, "caixa_x1_px": 220, "caixa_y1_px": 180,
         "crop_path": "/caminho/antigo/crop_a.png"},
        {**base, "imagem_id": "img1", "grupo_geometrico_id": "img1__0",
         "caixa_x0_px": 100, "caixa_y0_px": 100, "caixa_x1_px": 220, "caixa_y1_px": 180,
         "crop_path": "/caminho/antigo/crop_a.png"},   # mesmo crop repetido -> cache
        {**base, "imagem_id": "img2", "grupo_geometrico_id": "img2__0",
         "caixa_x0_px": 500, "caixa_y0_px": 700, "caixa_x1_px": 620, "caixa_y1_px": 780,
         "crop_path": "/caminho/antigo/crop_b.png"},
    ])
    return alvo, labels_dir, crops_dir


def test_tabela_tem_uma_linha_por_colagem_e_todas_as_features(tmp_path):
    alvo, labels_dir, crops_dir = _preparar(tmp_path)
    indice = construir_indice_crops([crops_dir])

    resumo = construir_tabela_features(alvo, labels_dir, indice, tmp_path / "tabela.csv")
    assert resumo["n_linhas"] == 3
    assert resumo["n_crops_unicos"] == 2       # crop_a usado 2x, crop_b 1x
    assert resumo["n_crops_nao_localizados"] == 0

    with open(tmp_path / "tabela.csv", newline="", encoding="utf-8") as f:
        linhas = list(csv.DictReader(f))
    for coluna in ("pos_v", "pos_h", "area_caixa_norm", "distorcao_aspect", "log_fator_reescala",
                   "coerencia_escala_pos", "nitidez", "contraste", "brilho_medio", "cobertura_mascara",
                   "acerto_votacao", "grupo_geometrico_id", "fonte"):
        assert coluna in linhas[0], f"faltou a coluna {coluna}"


def test_intrinsecas_vem_do_arquivo_certo(tmp_path):
    alvo, labels_dir, crops_dir = _preparar(tmp_path)
    indice = construir_indice_crops([crops_dir])
    construir_tabela_features(alvo, labels_dir, indice, tmp_path / "tabela.csv")

    with open(tmp_path / "tabela.csv", newline="", encoding="utf-8") as f:
        linhas = list(csv.DictReader(f))
    assert float(linhas[0]["brilho_medio"]) == 100.0  # crop_a
    assert float(linhas[2]["brilho_medio"]) == 200.0  # crop_b


def test_crop_nao_localizado_gera_intrinsecas_vazias_sem_quebrar(tmp_path):
    alvo, labels_dir, crops_dir = _preparar(tmp_path)
    indice = construir_indice_crops([crops_dir])
    del indice["crop_b.png"]  # simula crop ausente

    resumo = construir_tabela_features(alvo, labels_dir, indice, tmp_path / "tabela.csv")
    assert resumo["n_crops_nao_localizados"] == 1
    with open(tmp_path / "tabela.csv", newline="", encoding="utf-8") as f:
        linhas = list(csv.DictReader(f))
    assert linhas[2]["nitidez"] == ""   # vazio, não erro
    assert linhas[0]["nitidez"] != ""   # o localizado continua preenchido


def test_coerencia_e_identica_dentro_do_mesmo_grupo(tmp_path):
    """Geometria herdada: as duas variações da mesma caixa devem ter
    coerencia_escala_pos idêntica (§5.1 do plano)."""
    alvo, labels_dir, crops_dir = _preparar(tmp_path)
    indice = construir_indice_crops([crops_dir])
    construir_tabela_features(alvo, labels_dir, indice, tmp_path / "tabela.csv")

    with open(tmp_path / "tabela.csv", newline="", encoding="utf-8") as f:
        linhas = list(csv.DictReader(f))
    assert linhas[0]["coerencia_escala_pos"] == linhas[1]["coerencia_escala_pos"]
    assert linhas[0]["coerencia_escala_pos"] != linhas[2]["coerencia_escala_pos"]

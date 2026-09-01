"""Testes da tarefa -1.6 (terceira fonte, ABOShips): extração de crops a
partir do CSV com imagens distribuídas em subpastas de data."""
from __future__ import annotations

import csv
from pathlib import Path

import pytest
from PIL import Image

from src.extraction import extrair_crops_de_csv_abo, NomeBaseAmbiguo


def _criar_fonte_abo_sintetica(tmp_path: Path):
    """Reproduz a estrutura real: imagens em subpastas por data, CSV
    referenciando só o nome-base, múltiplas linhas por imagem possível."""
    imagens_dir = tmp_path / "images"
    (imagens_dir / "20180626").mkdir(parents=True)
    (imagens_dir / "20180627").mkdir(parents=True)

    Image.new("RGB", (1280, 720), color=(1, 1, 1)).save(imagens_dir / "20180626" / "201806260750_003.png")
    Image.new("RGB", (1280, 720), color=(2, 2, 2)).save(imagens_dir / "20180627" / "201806270800_001.png")

    caminho_csv = tmp_path / "Vesibussi_Labels.csv"
    linhas = [
        # duas caixas na mesma imagem (mesmo filename, duas linhas)
        {"filename": "201806260750_003", "width": 38, "height": 24, "class": "Boat",
         "xmin": 482, "xmax": 520, "ymin": 315, "ymax": 339},
        {"filename": "201806260750_003", "width": 10, "height": 8, "class": "Boat",
         "xmin": 100, "xmax": 110, "ymin": 200, "ymax": 208},
        {"filename": "201806270800_001", "width": 30, "height": 32, "class": "Boat",
         "xmin": 447, "xmax": 477, "ymin": 353, "ymax": 385},
    ]
    with open(caminho_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["filename", "width", "height", "class", "xmin", "xmax", "ymin", "ymax"])
        writer.writeheader()
        writer.writerows(linhas)

    return imagens_dir, caminho_csv


def test_extrai_crops_de_imagens_em_subpastas_de_data_diferentes(tmp_path):
    imagens_dir, caminho_csv = _criar_fonte_abo_sintetica(tmp_path)

    extraidos = extrair_crops_de_csv_abo(
        fonte="ABOShips", imagens_dir=imagens_dir, caminho_csv=caminho_csv,
        saida_crops_dir=tmp_path / "crops", manifesto_csv=tmp_path / "manifesto.csv",
    )
    assert len(extraidos) == 3  # 2 caixas na primeira imagem + 1 na segunda
    assert all(fonte == "ABOShips" for fonte, _ in extraidos)


def test_multiplas_caixas_na_mesma_imagem_tem_box_index_correto(tmp_path):
    imagens_dir, caminho_csv = _criar_fonte_abo_sintetica(tmp_path)
    manifesto_csv = tmp_path / "manifesto.csv"

    extrair_crops_de_csv_abo(
        fonte="ABOShips", imagens_dir=imagens_dir, caminho_csv=caminho_csv,
        saida_crops_dir=tmp_path / "crops", manifesto_csv=manifesto_csv,
    )

    with open(manifesto_csv, newline="", encoding="utf-8") as f:
        linhas = list(csv.DictReader(f))
    linhas_da_imagem_1 = [l for l in linhas if "201806260750_003" in l["imagem_origem"]]
    assert {l["box_index"] for l in linhas_da_imagem_1} == {"0", "1"}


def test_checagem_de_consistencia_width_height_confere_com_bbox(tmp_path):
    imagens_dir, caminho_csv = _criar_fonte_abo_sintetica(tmp_path)
    manifesto_csv = tmp_path / "manifesto.csv"

    extrair_crops_de_csv_abo(
        fonte="ABOShips", imagens_dir=imagens_dir, caminho_csv=caminho_csv,
        saida_crops_dir=tmp_path / "crops", manifesto_csv=manifesto_csv,
    )

    with open(manifesto_csv, newline="", encoding="utf-8") as f:
        linhas = list(csv.DictReader(f))
    # os dados sintéticos foram construídos para bater (mesma conta real do CSV verificado)
    assert all(l["width_height_csv_conferem_com_bbox"] == "True" for l in linhas)


def test_deteccao_de_inconsistencia_quando_width_nao_bate_com_bbox(tmp_path):
    imagens_dir = tmp_path / "images"
    imagens_dir.mkdir()
    Image.new("RGB", (1280, 720)).save(imagens_dir / "img1.png")

    caminho_csv = tmp_path / "labels.csv"
    with open(caminho_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["filename", "width", "height", "class", "xmin", "xmax", "ymin", "ymax"])
        writer.writeheader()
        # width=999 mas xmax-xmin=38 -- propositalmente inconsistente
        writer.writerow({"filename": "img1", "width": 999, "height": 24, "class": "Boat",
                          "xmin": 482, "xmax": 520, "ymin": 315, "ymax": 339})

    manifesto_csv = tmp_path / "manifesto.csv"
    extrair_crops_de_csv_abo(
        fonte="ABOShips", imagens_dir=imagens_dir, caminho_csv=caminho_csv,
        saida_crops_dir=tmp_path / "crops", manifesto_csv=manifesto_csv,
    )

    with open(manifesto_csv, newline="", encoding="utf-8") as f:
        linhas = list(csv.DictReader(f))
    assert linhas[0]["width_height_csv_conferem_com_bbox"] == "False"


def test_nome_base_ambiguo_entre_subpastas_de_data_e_detectado(tmp_path):
    imagens_dir = tmp_path / "images"
    (imagens_dir / "20180626").mkdir(parents=True)
    (imagens_dir / "20180627").mkdir(parents=True)
    # MESMO nome-base em duas subpastas de data diferentes -- caso ambíguo
    Image.new("RGB", (100, 100)).save(imagens_dir / "20180626" / "colisao.png")
    Image.new("RGB", (100, 100)).save(imagens_dir / "20180627" / "colisao.png")

    caminho_csv = tmp_path / "labels.csv"
    with open(caminho_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["filename", "width", "height", "class", "xmin", "xmax", "ymin", "ymax"])
        writer.writeheader()
        writer.writerow({"filename": "colisao", "width": 10, "height": 10, "class": "Boat",
                          "xmin": 0, "xmax": 10, "ymin": 0, "ymax": 10})

    with pytest.raises(NomeBaseAmbiguo):
        extrair_crops_de_csv_abo(
            fonte="ABOShips", imagens_dir=imagens_dir, caminho_csv=caminho_csv,
            saida_crops_dir=tmp_path / "crops", manifesto_csv=tmp_path / "manifesto.csv",
        )


def test_linha_do_csv_sem_imagem_correspondente_e_registrada(tmp_path):
    imagens_dir = tmp_path / "images"
    imagens_dir.mkdir()
    caminho_csv = tmp_path / "labels.csv"
    with open(caminho_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["filename", "width", "height", "class", "xmin", "xmax", "ymin", "ymax"])
        writer.writeheader()
        writer.writerow({"filename": "nao_existe", "width": 10, "height": 10, "class": "Boat",
                          "xmin": 0, "xmax": 10, "ymin": 0, "ymax": 10})

    manifesto_csv = tmp_path / "manifesto.csv"
    extraidos = extrair_crops_de_csv_abo(
        fonte="ABOShips", imagens_dir=imagens_dir, caminho_csv=caminho_csv,
        saida_crops_dir=tmp_path / "crops", manifesto_csv=manifesto_csv,
    )
    assert len(extraidos) == 0

    with open(manifesto_csv, newline="", encoding="utf-8") as f:
        linhas = list(csv.DictReader(f))
    assert linhas[0]["motivo"] == "imagem_nao_encontrada_no_indice"

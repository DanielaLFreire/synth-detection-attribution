"""Testes da tarefa -1.6 (primeira fonte, SMD): extração de crops a partir
de anotação YOLO, com captura de video_id."""
from __future__ import annotations

import csv
from pathlib import Path

from PIL import Image

from src.extraction import extrair_crops_de_yolo, identificar_video_id


class _SegmentadorFalsoParaTeste:
    """Marca metade esquerda de cada caixa como objeto -- suficiente para
    confirmar que o extrator está de fato chamando o segmentador e usando
    o resultado dele, sem precisar do SAM real."""
    def segmentar(self, imagem_rgb, caixa):
        import numpy as np
        mascara = np.zeros(imagem_rgb.shape[:2], dtype=bool)
        x0, y0, x1, y1 = caixa
        meio = x0 + (x1 - x0) // 2
        mascara[y0:y1, x0:meio] = True
        return mascara


def test_identificar_video_id_com_nomes_reais_do_smd():
    # nomes exatamente como vistos no smd_clean.zip real
    assert identificar_video_id("MVI_1486_VIS_frame540_jpg.rf.6b86ad6.txt") == "MVI_1486_VIS"
    assert identificar_video_id("MVI_1452_VIS_Haze_frame280_jpg.rf.528283.txt") == "MVI_1452_VIS_Haze"


def test_identificar_video_id_retorna_vazio_para_nome_nao_reconhecido():
    assert identificar_video_id("crop_qualquer_123.jpg") == ""


def _criar_fonte_yolo_sintetica(tmp_path: Path, especificacoes: dict[str, list[tuple[float, float, float, float]]]):
    """especificacoes: {stem: [(cx, cy, w, h), ...]}"""
    imagens_dir = tmp_path / "images"
    labels_dir = tmp_path / "labels"
    imagens_dir.mkdir(parents=True)
    labels_dir.mkdir(parents=True)

    for stem, boxes in especificacoes.items():
        Image.new("RGB", (200, 100), color=(5, 5, 5)).save(imagens_dir / f"{stem}.jpg")
        linhas = [f"0 {cx} {cy} {w} {h}" for cx, cy, w, h in boxes]
        (labels_dir / f"{stem}.txt").write_text("\n".join(linhas) + "\n")

    return imagens_dir, labels_dir


def test_extrai_um_crop_por_caixa(tmp_path):
    imagens_dir, labels_dir = _criar_fonte_yolo_sintetica(tmp_path, {
        "MVI_1486_VIS_frame540_jpg.rf.abc123": [(0.5, 0.5, 0.2, 0.3), (0.2, 0.2, 0.1, 0.1)],
        "MVI_1613_VIS_frame540_jpg.rf.def456": [(0.7, 0.3, 0.15, 0.15)],
    })

    extraidos = extrair_crops_de_yolo(
        fonte="SMD",
        imagens_dir=imagens_dir,
        labels_dir=labels_dir,
        saida_crops_dir=tmp_path / "crops_smd",
        manifesto_csv=tmp_path / "manifesto_extracao_yolo.csv",
    )

    assert len(extraidos) == 3  # 2 + 1 caixas
    assert all(fonte == "SMD" for fonte, _ in extraidos)
    for _, caminho in extraidos:
        assert caminho.exists()


def test_manifesto_captura_video_id_por_crop(tmp_path):
    imagens_dir, labels_dir = _criar_fonte_yolo_sintetica(tmp_path, {
        "MVI_1486_VIS_frame540_jpg.rf.abc123": [(0.5, 0.5, 0.2, 0.3)],
    })
    manifesto_csv = tmp_path / "manifesto.csv"

    extrair_crops_de_yolo(
        fonte="SMD", imagens_dir=imagens_dir, labels_dir=labels_dir,
        saida_crops_dir=tmp_path / "crops_smd", manifesto_csv=manifesto_csv,
    )

    with open(manifesto_csv, newline="", encoding="utf-8") as f:
        linhas = list(csv.DictReader(f))
    assert len(linhas) == 1
    assert linhas[0]["video_id"] == "MVI_1486_VIS"
    assert linhas[0]["extraido"] == "True"


def test_caixa_degenerada_e_pulada_sem_interromper_o_lote(tmp_path):
    imagens_dir, labels_dir = _criar_fonte_yolo_sintetica(tmp_path, {
        "img_com_caixa_degenerada": [(0.5, 0.5, 0.0, 0.0), (0.3, 0.3, 0.1, 0.1)],  # 1ª degenerada, 2ª ok
    })
    manifesto_csv = tmp_path / "manifesto.csv"

    extraidos = extrair_crops_de_yolo(
        fonte="FonteX", imagens_dir=imagens_dir, labels_dir=labels_dir,
        saida_crops_dir=tmp_path / "crops", manifesto_csv=manifesto_csv,
    )

    # só a caixa boa deve ter sido extraída -- o lote não foi interrompido
    assert len(extraidos) == 1

    with open(manifesto_csv, newline="", encoding="utf-8") as f:
        linhas = list(csv.DictReader(f))
    assert len(linhas) == 2  # ambas registradas, uma com extraido=False
    degenerada = next(l for l in linhas if l["box_index"] == "0")
    assert degenerada["extraido"] == "False"
    assert degenerada["motivo"] == "bbox_degenerada"


def test_label_sem_imagem_correspondente_e_registrado_nao_interrompe(tmp_path):
    imagens_dir, labels_dir = _criar_fonte_yolo_sintetica(tmp_path, {"img_ok": [(0.5, 0.5, 0.1, 0.1)]})
    # cria um label extra sem imagem correspondente
    (labels_dir / "img_orfao.txt").write_text("0 0.5 0.5 0.1 0.1\n")
    manifesto_csv = tmp_path / "manifesto.csv"

    extraidos = extrair_crops_de_yolo(
        fonte="FonteX", imagens_dir=imagens_dir, labels_dir=labels_dir,
        saida_crops_dir=tmp_path / "crops", manifesto_csv=manifesto_csv,
    )
    assert len(extraidos) == 1  # só a imagem que existe

    with open(manifesto_csv, newline="", encoding="utf-8") as f:
        linhas = list(csv.DictReader(f))
    orfao = next(l for l in linhas if "img_orfao" in l["imagem_origem"])
    assert orfao["motivo"] == "imagem_nao_encontrada"


def test_com_segmentador_saida_e_sempre_png_com_alpha(tmp_path):
    imagens_dir, labels_dir = _criar_fonte_yolo_sintetica(tmp_path, {
        "img_teste": [(0.5, 0.5, 0.4, 0.4)],
    })

    extraidos = extrair_crops_de_yolo(
        fonte="SMD", imagens_dir=imagens_dir, labels_dir=labels_dir,
        saida_crops_dir=tmp_path / "crops_segmentados",
        manifesto_csv=tmp_path / "manifesto_seg.csv",
        extensao_imagem=".jpg",  # pedido .jpg, mas com segmentador deve sair .png
        segmentador=_SegmentadorFalsoParaTeste(),
    )

    assert len(extraidos) == 1
    _, caminho_crop = extraidos[0]
    assert caminho_crop.suffix == ".png"
    with Image.open(caminho_crop) as img_salva:
        assert img_salva.mode == "RGBA"


def test_com_segmentador_manifesto_registra_cobertura_mascara(tmp_path):
    imagens_dir, labels_dir = _criar_fonte_yolo_sintetica(tmp_path, {
        "img_teste": [(0.5, 0.5, 0.4, 0.4)],
    })
    manifesto_csv = tmp_path / "manifesto_seg.csv"

    extrair_crops_de_yolo(
        fonte="SMD", imagens_dir=imagens_dir, labels_dir=labels_dir,
        saida_crops_dir=tmp_path / "crops_segmentados",
        manifesto_csv=manifesto_csv,
        segmentador=_SegmentadorFalsoParaTeste(),
    )

    with open(manifesto_csv, newline="", encoding="utf-8") as f:
        linhas = list(csv.DictReader(f))
    # segmentador falso marca metade da caixa -- cobertura deve ser ~0.5
    assert abs(float(linhas[0]["cobertura_mascara"]) - 0.5) < 0.05


def test_sem_segmentador_cobertura_mascara_fica_vazia(tmp_path):
    """Confirma que o modo antigo (retangular, sem segmentador) continua
    preenchendo o novo campo como vazio, não quebrando a leitura do CSV."""
    imagens_dir, labels_dir = _criar_fonte_yolo_sintetica(tmp_path, {
        "img_teste": [(0.5, 0.5, 0.2, 0.2)],
    })
    manifesto_csv = tmp_path / "manifesto.csv"

    extrair_crops_de_yolo(
        fonte="SMD", imagens_dir=imagens_dir, labels_dir=labels_dir,
        saida_crops_dir=tmp_path / "crops", manifesto_csv=manifesto_csv,
    )

    with open(manifesto_csv, newline="", encoding="utf-8") as f:
        linhas = list(csv.DictReader(f))
    assert linhas[0]["cobertura_mascara"] == ""

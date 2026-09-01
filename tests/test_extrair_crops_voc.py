"""Testes da tarefa -1.6 (segunda fonte, SeaShips): extração de crops a
partir de anotação VOC XML."""
from __future__ import annotations

import csv
from pathlib import Path

from PIL import Image

from src.extraction import extrair_crops_de_voc


def _xml_voc(largura_declarada: int, altura_declarada: int, objetos: list[tuple[str, int, int, int, int]]) -> str:
    objs_xml = "\n".join(
        f"""
        <object>
            <name>{classe}</name>
            <bndbox>
                <xmin>{xmin}</xmin><ymin>{ymin}</ymin>
                <xmax>{xmax}</xmax><ymax>{ymax}</ymax>
            </bndbox>
        </object>"""
        for classe, xmin, ymin, xmax, ymax in objetos
    )
    return f"""<annotation>
        <size><width>{largura_declarada}</width><height>{altura_declarada}</height></size>
        {objs_xml}
    </annotation>"""


def _criar_fonte_voc_sintetica(tmp_path: Path, especificacoes: dict):
    """especificacoes: {stem: {"tamanho_real": (w,h), "tamanho_xml": (w,h), "objetos": [(classe,x0,y0,x1,y1),...]}}"""
    imagens_dir = tmp_path / "images"
    anotacoes_dir = tmp_path / "annotations"
    imagens_dir.mkdir(parents=True)
    anotacoes_dir.mkdir(parents=True)

    for stem, spec in especificacoes.items():
        Image.new("RGB", spec["tamanho_real"], color=(9, 9, 9)).save(imagens_dir / f"{stem}.jpg")
        xml = _xml_voc(*spec["tamanho_xml"], spec["objetos"])
        (anotacoes_dir / f"{stem}.xml").write_text(xml)

    return imagens_dir, anotacoes_dir


def test_extrai_um_crop_por_objeto(tmp_path):
    imagens_dir, anotacoes_dir = _criar_fonte_voc_sintetica(tmp_path, {
        "img1": {
            "tamanho_real": (200, 100), "tamanho_xml": (200, 100),
            "objetos": [("ore carrier", 10, 10, 60, 50), ("fishing boat", 100, 20, 150, 70)],
        },
    })

    extraidos = extrair_crops_de_voc(
        fonte="SeaShips", imagens_dir=imagens_dir, anotacoes_dir=anotacoes_dir,
        saida_crops_dir=tmp_path / "crops", manifesto_csv=tmp_path / "manifesto.csv",
    )
    assert len(extraidos) == 2
    assert all(fonte == "SeaShips" for fonte, _ in extraidos)


def test_manifesto_preserva_classe_original_da_fonte(tmp_path):
    imagens_dir, anotacoes_dir = _criar_fonte_voc_sintetica(tmp_path, {
        "img1": {
            "tamanho_real": (200, 100), "tamanho_xml": (200, 100),
            "objetos": [("container ship", 10, 10, 60, 50)],
        },
    })
    manifesto_csv = tmp_path / "manifesto.csv"

    extrair_crops_de_voc(
        fonte="SeaShips", imagens_dir=imagens_dir, anotacoes_dir=anotacoes_dir,
        saida_crops_dir=tmp_path / "crops", manifesto_csv=manifesto_csv,
    )

    with open(manifesto_csv, newline="", encoding="utf-8") as f:
        linhas = list(csv.DictReader(f))
    assert linhas[0]["classe_original_fonte"] == "container ship"


def test_deteccao_de_divergencia_entre_dimensoes_xml_e_imagem_real(tmp_path):
    imagens_dir, anotacoes_dir = _criar_fonte_voc_sintetica(tmp_path, {
        "img_divergente": {
            "tamanho_real": (200, 100),   # imagem real é 200x100
            "tamanho_xml": (400, 200),    # mas o XML declara 400x200 -- divergência
            "objetos": [("ore carrier", 10, 10, 60, 50)],
        },
        "img_ok": {
            "tamanho_real": (200, 100), "tamanho_xml": (200, 100),
            "objetos": [("ore carrier", 10, 10, 60, 50)],
        },
    })
    manifesto_csv = tmp_path / "manifesto.csv"

    extrair_crops_de_voc(
        fonte="SeaShips", imagens_dir=imagens_dir, anotacoes_dir=anotacoes_dir,
        saida_crops_dir=tmp_path / "crops", manifesto_csv=manifesto_csv,
    )

    with open(manifesto_csv, newline="", encoding="utf-8") as f:
        linhas = list(csv.DictReader(f))
    divergente = next(l for l in linhas if "img_divergente" in l["imagem_origem"])
    ok = next(l for l in linhas if "img_ok" in l["imagem_origem"])
    assert divergente["dimensoes_xml_conferem_com_imagem"] == "False"
    assert ok["dimensoes_xml_conferem_com_imagem"] == "True"


def test_caixa_degenerada_e_pulada_sem_interromper_o_lote(tmp_path):
    imagens_dir, anotacoes_dir = _criar_fonte_voc_sintetica(tmp_path, {
        "img1": {
            "tamanho_real": (200, 100), "tamanho_xml": (200, 100),
            "objetos": [("ore carrier", 50, 50, 50, 50), ("ore carrier", 10, 10, 60, 50)],  # 1ª degenerada
        },
    })
    manifesto_csv = tmp_path / "manifesto.csv"

    extraidos = extrair_crops_de_voc(
        fonte="SeaShips", imagens_dir=imagens_dir, anotacoes_dir=anotacoes_dir,
        saida_crops_dir=tmp_path / "crops", manifesto_csv=manifesto_csv,
    )
    assert len(extraidos) == 1  # só a 2ª caixa, válida

    with open(manifesto_csv, newline="", encoding="utf-8") as f:
        linhas = list(csv.DictReader(f))
    degenerada = next(l for l in linhas if l["box_index"] == "0")
    assert degenerada["motivo"] == "bbox_degenerada"

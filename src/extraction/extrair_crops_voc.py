"""
Extração de crops a partir de anotação VOC XML (tarefa -1.6, segunda fonte:
SeaShips).

Diferença em relação a extrair_crops_yolo.py: VOC guarda a caixa em pixels
ABSOLUTOS (xmin, ymin, xmax, ymax), não normalizados -- não há conversão por
dimensão de imagem. Cada <object> carrega um <name> com a subclasse
original do SeaShips (6 tipos de embarcação no dataset original) -- como
este projeto usa o SeaShips apenas como fonte de aparência visual para a
classe única do dataset-alvo, extraímos TODO objeto anotado independente da
subclasse, mas registramos a subclasse original no manifesto (útil para a
descrição do dataset no artigo, não usada para filtrar).

Checagem de auditoria incluída: VOC XML normalmente also guarda <width>/
<height> da imagem dentro do próprio XML -- comparamos com o tamanho real
do arquivo de imagem e sinalizamos (não abortamos) divergência.
"""
from __future__ import annotations

import csv
import xml.etree.ElementTree as ET
from dataclasses import dataclass, fields, asdict
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

EXTRACAO_VOC_MANIFEST_VERSION = "1.0"


@dataclass
class LinhaExtracaoVoc:
    manifest_version: str
    run_id: str
    timestamp_extracao: str
    fonte: str
    imagem_origem: str
    box_index: int
    classe_original_fonte: str
    largura_px: int
    altura_px: int
    dimensoes_xml_conferem_com_imagem: str  # "True"/"False"/"" (quando XML não tem size)
    extraido: bool
    motivo: str
    caminho_crop: str


_FIELDNAMES = [f.name for f in fields(LinhaExtracaoVoc)]


@dataclass
class _ObjetoVoc:
    classe: str
    xmin: int
    ymin: int
    xmax: int
    ymax: int


def _ler_objetos_voc(caminho_xml: Path) -> tuple[list[_ObjetoVoc], tuple[int, int] | None]:
    """Retorna (objetos, (largura_xml, altura_xml) ou None se ausente)."""
    tree = ET.parse(caminho_xml)
    root = tree.getroot()

    tamanho_xml = None
    size_el = root.find("size")
    if size_el is not None:
        w_el, h_el = size_el.find("width"), size_el.find("height")
        if w_el is not None and h_el is not None:
            tamanho_xml = (int(float(w_el.text)), int(float(h_el.text)))

    objetos = []
    for obj in root.findall("object"):
        nome_el = obj.find("name")
        classe = nome_el.text.strip() if nome_el is not None and nome_el.text else "desconhecida"
        bndbox = obj.find("bndbox")
        if bndbox is None:
            continue
        xmin = int(float(bndbox.find("xmin").text))
        ymin = int(float(bndbox.find("ymin").text))
        xmax = int(float(bndbox.find("xmax").text))
        ymax = int(float(bndbox.find("ymax").text))
        objetos.append(_ObjetoVoc(classe=classe, xmin=xmin, ymin=ymin, xmax=xmax, ymax=ymax))

    return objetos, tamanho_xml


def extrair_crops_de_voc(
    *,
    fonte: str,
    imagens_dir: Path,
    anotacoes_dir: Path,
    saida_crops_dir: Path,
    manifesto_csv: Path,
    extensao_imagem: str = ".jpg",
) -> list[tuple[str, Path]]:
    """Extrai um arquivo de crop por <object> de cada anotação VOC XML.

    Mesma filosofia de tolerância do extrator YOLO (-1.6, SMD): caixa
    degenerada ou órfão são pulados e registrados, não interrompem o lote.
    """
    imagens_dir = Path(imagens_dir)
    anotacoes_dir = Path(anotacoes_dir)
    saida_crops_dir = Path(saida_crops_dir)
    saida_crops_dir.mkdir(parents=True, exist_ok=True)
    manifesto_csv = Path(manifesto_csv)
    manifesto_csv.parent.mkdir(parents=True, exist_ok=True)

    run_id = datetime.now(timezone.utc).strftime("extracao_voc_%Y%m%dT%H%M%SZ")
    extraidos: list[tuple[str, Path]] = []

    anotacoes = sorted(anotacoes_dir.glob("*.xml"))

    with open(manifesto_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_FIELDNAMES)
        writer.writeheader()

        for caminho_xml in anotacoes:
            stem = caminho_xml.stem
            caminho_imagem = imagens_dir / f"{stem}{extensao_imagem}"

            if not caminho_imagem.exists():
                writer.writerow(asdict(LinhaExtracaoVoc(
                    manifest_version=EXTRACAO_VOC_MANIFEST_VERSION,
                    run_id=run_id, timestamp_extracao=datetime.now(timezone.utc).isoformat(),
                    fonte=fonte, imagem_origem=str(caminho_imagem), box_index=-1,
                    classe_original_fonte="", largura_px=0, altura_px=0,
                    dimensoes_xml_conferem_com_imagem="",
                    extraido=False, motivo="imagem_nao_encontrada", caminho_crop="",
                )))
                continue

            objetos, tamanho_xml = _ler_objetos_voc(caminho_xml)

            with Image.open(caminho_imagem) as img:
                tamanho_real = img.size
                conferem = "" if tamanho_xml is None else str(tamanho_xml == tamanho_real)

                for i, obj in enumerate(objetos):
                    x0, y0 = max(0, obj.xmin), max(0, obj.ymin)
                    x1, y1 = min(tamanho_real[0], obj.xmax), min(tamanho_real[1], obj.ymax)

                    if x1 - x0 <= 0 or y1 - y0 <= 0:
                        writer.writerow(asdict(LinhaExtracaoVoc(
                            manifest_version=EXTRACAO_VOC_MANIFEST_VERSION,
                            run_id=run_id, timestamp_extracao=datetime.now(timezone.utc).isoformat(),
                            fonte=fonte, imagem_origem=str(caminho_imagem), box_index=i,
                            classe_original_fonte=obj.classe, largura_px=0, altura_px=0,
                            dimensoes_xml_conferem_com_imagem=conferem,
                            extraido=False, motivo="bbox_degenerada", caminho_crop="",
                        )))
                        continue

                    crop = img.crop((x0, y0, x1, y1))
                    caminho_crop = saida_crops_dir / f"{stem}_box{i:03d}{extensao_imagem}"
                    crop.save(caminho_crop)

                    writer.writerow(asdict(LinhaExtracaoVoc(
                        manifest_version=EXTRACAO_VOC_MANIFEST_VERSION,
                        run_id=run_id, timestamp_extracao=datetime.now(timezone.utc).isoformat(),
                        fonte=fonte, imagem_origem=str(caminho_imagem), box_index=i,
                        classe_original_fonte=obj.classe, largura_px=x1 - x0, altura_px=y1 - y0,
                        dimensoes_xml_conferem_com_imagem=conferem,
                        extraido=True, motivo="ok", caminho_crop=str(caminho_crop),
                    )))
                    extraidos.append((fonte, caminho_crop))

    return extraidos

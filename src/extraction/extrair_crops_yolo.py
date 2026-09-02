"""
Extração de crops a partir de anotação YOLO (tarefa -1.6, primeira fonte: SMD).

Diferença em relação a src/extraction/quality_filter.py e quality_manifest.py:
aqueles módulos operam sobre crops JÁ EXTRAÍDOS (decidem manter/descartar).
Este módulo faz a extração em si: lê a anotação (classe cx cy w h
normalizados) e recorta a região da bounding box da imagem original,
salvando cada caixa como um arquivo de crop individual.

Modo de extração: recorte retangular por padrão, OU segmentação (via
parâmetro `segmentador`, ver src/segmentation/) -- decisão registrada em
docs/CHANGELOG_metodologico.md (2026-09-01): recorte retangular puro corre
risco de "shortcut learning" (Geirhos et al., 2020) via borda de colagem
visível, então a segmentação passa a ser o modo recomendado quando
disponível. Quando `segmentador` é fornecido, a segmentação roda SEMPRE
sobre a imagem original (nunca sobre um crop já recortado) -- ver docstring
de src/segmentation/sam_segment.py para a justificativa. Nesse modo, a
saída é sempre .png (precisa de canal alpha), independente de
`extensao_imagem`.

Achado que motiva o campo `video_id` no manifesto: as imagens do SMD são
frames extraídos de vídeo (36 vídeos distintos, ~11-35 frames cada) --
frames do mesmo vídeo são mais parecidos entre si do que frames de vídeos
diferentes (mesma cena, câmera com pouco deslocamento entre frames
vizinhos). Isso é uma forma de quase-duplicação por CONTEÚDO, distinta mas
análoga em efeito à duplicação por augmentation do Roboflow encontrada no
SeaShips -- capturado aqui para permitir análise/agrupamento futuro, mesmo
que a decisão de como tratar isso (ex.: amostrar no máximo N crops por
vídeo) ainda não tenha sido tomada.
"""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass, fields, asdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image

from src.segmentation import Segmentador, aplicar_mascara_e_recortar

EXTRACAO_YOLO_MANIFEST_VERSION = "1.1"  # bump: campo cobertura_mascara adicionado

# Padrão de nome de arquivo do SMD: "MVI_1486_VIS_frame540_jpg.rf.<hash>.jpg"
# ou variantes com "_Haze" / "_NIR". Generalizado o suficiente para outras
# fontes baseadas em vídeo, mas verificado especificamente contra o SMD.
_PADRAO_VIDEO_ID = re.compile(r"^(MVI_\d+(?:_VIS|_NIR)?(?:_Haze)?)_frame")


@dataclass
class LinhaExtracaoYolo:
    manifest_version: str
    run_id: str
    timestamp_extracao: str
    fonte: str
    imagem_origem: str
    box_index: int
    video_id: str  # "" quando não aplicável/não reconhecido -- nunca None (CSV-friendly)
    largura_px: int
    altura_px: int
    extraido: bool
    motivo: str
    caminho_crop: str  # "" quando extraido=False
    cobertura_mascara: str = ""  # "" quando modo retangular (sem segmentador)


_FIELDNAMES = [f.name for f in fields(LinhaExtracaoYolo)]


def identificar_video_id(nome_arquivo: str) -> str:
    """Extrai o id do vídeo de origem do nome do arquivo, se reconhecível.
    Retorna string vazia (não None) quando não reconhece -- explícito e
    fácil de filtrar num CSV depois."""
    m = _PADRAO_VIDEO_ID.match(nome_arquivo)
    return m.group(1) if m else ""


def _ler_boxes_yolo(caminho_label: Path) -> list[tuple[str, float, float, float, float]]:
    boxes = []
    with open(caminho_label, "r", encoding="utf-8") as f:
        for linha in f:
            partes = linha.split()
            if len(partes) < 5:
                continue
            classe, cx, cy, w, h = partes[:5]
            boxes.append((classe, float(cx), float(cy), float(w), float(h)))
    return boxes


def extrair_crops_de_yolo(
    *,
    fonte: str,
    imagens_dir: Path,
    labels_dir: Path,
    saida_crops_dir: Path,
    manifesto_csv: Path,
    extensao_imagem: str = ".jpg",
    segmentador: Segmentador | None = None,
) -> list[tuple[str, Path]]:
    """Extrai um arquivo de crop por bounding box, a partir de anotação
    YOLO. Caixas degeneradas (largura ou altura <= 0 pixels após conversão)
    são puladas e registradas no manifesto com extraido=False -- não
    interrompem a extração das demais (ao contrário da materialização de
    labels_final, que é estrita por lidar com o dataset-alvo; aqui lidamos
    com uma fonte de crops, onde uma caixa ruim isolada não compromete o
    experimento, só reduz o pool em uma unidade).

    `segmentador`: se fornecido (ex.: SegmentadorSAM), cada caixa é
    segmentada sobre a IMAGEM ORIGINAL antes do recorte -- produz crops
    RGBA com fundo isolado, salvos sempre como .png. Se None (padrão),
    comportamento antigo: recorte retangular direto.

    Retorna a lista de crops extraídos no formato (fonte, caminho) --
    ainda precisa passar pelo filtro de qualidade unificado (-1.3) antes de
    entrar no pool final do composer.
    """
    imagens_dir = Path(imagens_dir)
    labels_dir = Path(labels_dir)
    saida_crops_dir = Path(saida_crops_dir)
    saida_crops_dir.mkdir(parents=True, exist_ok=True)
    manifesto_csv = Path(manifesto_csv)
    manifesto_csv.parent.mkdir(parents=True, exist_ok=True)

    ext_saida = ".png" if segmentador is not None else extensao_imagem

    run_id = datetime.now(timezone.utc).strftime("extracao_yolo_%Y%m%dT%H%M%SZ")
    extraidos: list[tuple[str, Path]] = []

    labels = sorted(labels_dir.glob("*.txt"))

    with open(manifesto_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_FIELDNAMES)
        writer.writeheader()

        for caminho_label in labels:
            stem = caminho_label.stem
            caminho_imagem = imagens_dir / f"{stem}{extensao_imagem}"
            video_id = identificar_video_id(stem)

            if not caminho_imagem.exists():
                # órfão: label sem imagem -- registrado, não interrompe o lote
                writer.writerow(asdict(LinhaExtracaoYolo(
                    manifest_version=EXTRACAO_YOLO_MANIFEST_VERSION,
                    run_id=run_id, timestamp_extracao=datetime.now(timezone.utc).isoformat(),
                    fonte=fonte, imagem_origem=str(caminho_imagem), box_index=-1,
                    video_id=video_id, largura_px=0, altura_px=0,
                    extraido=False, motivo="imagem_nao_encontrada", caminho_crop="",
                )))
                continue

            with Image.open(caminho_imagem) as img:
                largura_img, altura_img = img.size
                boxes = _ler_boxes_yolo(caminho_label)
                img_np = np.array(img.convert("RGB")) if segmentador is not None else None

                for i, (classe, cx, cy, w, h) in enumerate(boxes):
                    bw_px = w * largura_img
                    bh_px = h * altura_img
                    x0 = round(cx * largura_img - bw_px / 2)
                    y0 = round(cy * altura_img - bh_px / 2)
                    x1 = round(x0 + bw_px)
                    y1 = round(y0 + bh_px)
                    x0, y0 = max(0, x0), max(0, y0)
                    x1, y1 = min(largura_img, x1), min(altura_img, y1)

                    if x1 - x0 <= 0 or y1 - y0 <= 0:
                        writer.writerow(asdict(LinhaExtracaoYolo(
                            manifest_version=EXTRACAO_YOLO_MANIFEST_VERSION,
                            run_id=run_id, timestamp_extracao=datetime.now(timezone.utc).isoformat(),
                            fonte=fonte, imagem_origem=str(caminho_imagem), box_index=i,
                            video_id=video_id, largura_px=0, altura_px=0,
                            extraido=False, motivo="bbox_degenerada", caminho_crop="",
                        )))
                        continue

                    caminho_crop = saida_crops_dir / f"{stem}_box{i:03d}{ext_saida}"
                    cobertura_str = ""

                    if segmentador is not None:
                        mascara = segmentador.segmentar(img_np, (x0, y0, x1, y1))
                        resultado = aplicar_mascara_e_recortar(img_np, (x0, y0, x1, y1), mascara)
                        resultado.crop_rgba.save(caminho_crop)
                        cobertura_str = f"{resultado.cobertura_mascara:.4f}"
                    else:
                        crop = img.crop((x0, y0, x1, y1))
                        crop.save(caminho_crop)

                    writer.writerow(asdict(LinhaExtracaoYolo(
                        manifest_version=EXTRACAO_YOLO_MANIFEST_VERSION,
                        run_id=run_id, timestamp_extracao=datetime.now(timezone.utc).isoformat(),
                        fonte=fonte, imagem_origem=str(caminho_imagem), box_index=i,
                        video_id=video_id, largura_px=x1 - x0, altura_px=y1 - y0,
                        extraido=True, motivo="ok", caminho_crop=str(caminho_crop),
                        cobertura_mascara=cobertura_str,
                    )))
                    extraidos.append((fonte, caminho_crop))

    return extraidos


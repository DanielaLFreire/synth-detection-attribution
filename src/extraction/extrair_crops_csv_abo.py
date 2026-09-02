"""
Extração de crops a partir do CSV de anotação do ABOShips (tarefa -1.6,
terceira fonte).

Formato verificado em 2026-09-01 (não assumido de documentação antiga):
`Vesibussi_Labels.csv`, colunas `filename,width,height,class,xmin,xmax,ymin,ymax`.

Dois achados confirmados por verificação direta:
1. `width`/`height` são as dimensões da CAIXA (xmax-xmin, ymax-ymin),
   não da imagem -- confirmado numericamente (ver
   docs/CHANGELOG_metodologico.md). Redundantes com xmin/xmax/ymin/ymax;
   usadas aqui só como checagem de consistência, não como fonte de verdade.
2. A suposição herdada de "imagem sempre 1280x720" foi verificada em
   apenas 5 de 9.880 imagens -- este extrator NUNCA assume essa dimensão;
   sempre abre a imagem real para obter as dimensões.

Particularidade estrutural: o CSV referencia imagens só pelo nome-base
(sem subpasta de data, sem extensão) -- as imagens estão distribuídas em
16 subpastas por data dentro do zip. Este módulo indexa todas as imagens
por nome-base antes de processar o CSV.

Modo de extração: recorte retangular por padrão, OU segmentação (via
parâmetro `segmentador`) -- mesmo padrão dos outros dois extratores, ver
docstring de extrair_crops_yolo.py e src/segmentation/sam_segment.py.
Este extrator já salvava sempre em .png (independente do segmentador), por
isso a saída já é compatível com canal alpha sem mudança adicional.
"""
from __future__ import annotations

import csv as csv_module
from collections import defaultdict
from dataclasses import dataclass, fields, asdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image

from src.segmentation import Segmentador, aplicar_mascara_e_recortar

EXTRACAO_CSV_ABO_MANIFEST_VERSION = "1.1"  # bump: campo cobertura_mascara adicionado
_EXTENSOES_IMAGEM = (".png", ".jpg", ".jpeg")


@dataclass
class LinhaExtracaoCsvAbo:
    manifest_version: str
    run_id: str
    timestamp_extracao: str
    fonte: str
    imagem_origem: str
    box_index: int
    classe_original_fonte: str
    largura_px: int
    altura_px: int
    width_height_csv_conferem_com_bbox: str  # "True"/"False" -- checagem de consistência
    extraido: bool
    motivo: str
    caminho_crop: str
    cobertura_mascara: str = ""  # "" quando modo retangular (sem segmentador)


_FIELDNAMES = [f.name for f in fields(LinhaExtracaoCsvAbo)]


class NomeBaseAmbiguo(RuntimeError):
    """Levantado se duas imagens em subpastas de data diferentes tiverem o
    mesmo nome-base -- indicaria que a indexação por nome-base sozinho não
    é segura, e precisaríamos incluir a subpasta na chave."""


def _indexar_imagens_por_stem(imagens_dir: Path) -> dict[str, Path]:
    indice: dict[str, Path] = {}
    for caminho in Path(imagens_dir).rglob("*"):
        if caminho.is_file() and caminho.suffix.lower() in _EXTENSOES_IMAGEM:
            if caminho.stem in indice and indice[caminho.stem] != caminho:
                raise NomeBaseAmbiguo(
                    f"nome-base '{caminho.stem}' aparece em mais de um lugar: "
                    f"{indice[caminho.stem]} e {caminho} -- indexação por "
                    "nome-base sozinho não é segura para este dataset."
                )
            indice[caminho.stem] = caminho
    return indice


def extrair_crops_de_csv_abo(
    *,
    fonte: str,
    imagens_dir: Path,
    caminho_csv: Path,
    saida_crops_dir: Path,
    manifesto_csv: Path,
    segmentador: Segmentador | None = None,
) -> list[tuple[str, Path]]:
    imagens_dir = Path(imagens_dir)
    saida_crops_dir = Path(saida_crops_dir)
    saida_crops_dir.mkdir(parents=True, exist_ok=True)
    manifesto_csv = Path(manifesto_csv)
    manifesto_csv.parent.mkdir(parents=True, exist_ok=True)

    indice_imagens = _indexar_imagens_por_stem(imagens_dir)

    # agrupa linhas do CSV por filename, preservando ordem -- box_index é a
    # posição dentro do grupo, não uma contagem corrida (mais robusto a
    # CSVs não ordenados por filename)
    grupos: dict[str, list[dict]] = defaultdict(list)
    with open(caminho_csv, "r", encoding="utf-8", newline="") as f:
        for linha in csv_module.DictReader(f):
            grupos[linha["filename"]].append(linha)

    run_id = datetime.now(timezone.utc).strftime("extracao_csv_abo_%Y%m%dT%H%M%SZ")
    extraidos: list[tuple[str, Path]] = []

    with open(manifesto_csv, "w", newline="", encoding="utf-8") as f_out:
        writer = csv_module.DictWriter(f_out, fieldnames=_FIELDNAMES)
        writer.writeheader()

        for filename, linhas in grupos.items():
            caminho_imagem = indice_imagens.get(filename)
            if caminho_imagem is None:
                writer.writerow(asdict(LinhaExtracaoCsvAbo(
                    manifest_version=EXTRACAO_CSV_ABO_MANIFEST_VERSION,
                    run_id=run_id, timestamp_extracao=datetime.now(timezone.utc).isoformat(),
                    fonte=fonte, imagem_origem=filename, box_index=-1,
                    classe_original_fonte="", largura_px=0, altura_px=0,
                    width_height_csv_conferem_com_bbox="",
                    extraido=False, motivo="imagem_nao_encontrada_no_indice", caminho_crop="",
                )))
                continue

            with Image.open(caminho_imagem) as img:
                tamanho_real = img.size  # sempre lido da imagem real, nunca assumido
                img_np = np.array(img.convert("RGB")) if segmentador is not None else None

                for i, linha in enumerate(linhas):
                    xmin, xmax = int(linha["xmin"]), int(linha["xmax"])
                    ymin, ymax = int(linha["ymin"]), int(linha["ymax"])
                    width_csv, height_csv = int(linha["width"]), int(linha["height"])
                    classe = linha.get("class", "desconhecida")

                    conferem = (width_csv == xmax - xmin) and (height_csv == ymax - ymin)

                    x0, y0 = max(0, xmin), max(0, ymin)
                    x1, y1 = min(tamanho_real[0], xmax), min(tamanho_real[1], ymax)

                    if x1 - x0 <= 0 or y1 - y0 <= 0:
                        writer.writerow(asdict(LinhaExtracaoCsvAbo(
                            manifest_version=EXTRACAO_CSV_ABO_MANIFEST_VERSION,
                            run_id=run_id, timestamp_extracao=datetime.now(timezone.utc).isoformat(),
                            fonte=fonte, imagem_origem=str(caminho_imagem), box_index=i,
                            classe_original_fonte=classe, largura_px=0, altura_px=0,
                            width_height_csv_conferem_com_bbox=str(conferem),
                            extraido=False, motivo="bbox_degenerada", caminho_crop="",
                        )))
                        continue

                    caminho_crop = saida_crops_dir / f"{filename}_box{i:03d}.png"
                    cobertura_str = ""

                    if segmentador is not None:
                        mascara = segmentador.segmentar(img_np, (x0, y0, x1, y1))
                        resultado = aplicar_mascara_e_recortar(img_np, (x0, y0, x1, y1), mascara)
                        resultado.crop_rgba.save(caminho_crop)
                        cobertura_str = f"{resultado.cobertura_mascara:.4f}"
                    else:
                        crop = img.crop((x0, y0, x1, y1))
                        crop.save(caminho_crop)

                    writer.writerow(asdict(LinhaExtracaoCsvAbo(
                        manifest_version=EXTRACAO_CSV_ABO_MANIFEST_VERSION,
                        run_id=run_id, timestamp_extracao=datetime.now(timezone.utc).isoformat(),
                        fonte=fonte, imagem_origem=str(caminho_imagem), box_index=i,
                        classe_original_fonte=classe, largura_px=x1 - x0, altura_px=y1 - y0,
                        width_height_csv_conferem_com_bbox=str(conferem),
                        extraido=True, motivo="ok", caminho_crop=str(caminho_crop),
                        cobertura_mascara=cobertura_str,
                    )))
                    extraidos.append((fonte, caminho_crop))

    return extraidos

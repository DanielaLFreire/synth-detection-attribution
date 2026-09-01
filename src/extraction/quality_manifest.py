"""
Manifesto de extração de crops (§8.1/§12.1 do plano) e a função que aplica
o filtro unificado (quality_filter.py) sobre um diretório de crops já
extraídos de uma fonte, produzindo o pool no formato que
src.compose.compor_dataset espera: list[(nome_da_fonte, caminho_do_crop)].

Escopo desta versão: opera sobre crops JÁ EXTRAÍDOS (arquivos de imagem
individuais, um por crop). A extração a partir da anotação nativa de cada
fonte (CSV do ABOShips, XML do SeaShips, etc.) é responsabilidade de um
módulo por fonte, ainda não escrito para ABOShips/SMD -- ver
docs/CHANGELOG_metodologico.md para o escopo explícito desta entrega.
"""
from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass, fields, asdict
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

from .quality_filter import FiltroConfig, avaliar_crop

MANIFEST_EXTRACAO_VERSION = "1.0"

_EXTENSOES_IMAGEM = (".png", ".jpg", ".jpeg")


@dataclass
class LinhaManifestoExtracao:
    manifest_version: str
    run_id: str
    timestamp_avaliacao: str
    fonte: str
    caminho_crop: str
    largura_px: int
    altura_px: int
    cobertura_mascara: str  # string porque pode ser "" (None) -- CSV não tem NaN nativo
    mantido: bool
    motivo: str
    sha256: str  # só calculado para crops mantidos; "" para descartados


_FIELDNAMES = [f.name for f in fields(LinhaManifestoExtracao)]


def _sha256_arquivo(caminho: Path) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(65536), b""):
            h.update(bloco)
    return h.hexdigest()


def filtrar_pool_de_crops(
    *,
    fonte: str,
    crops_dir: Path,
    config: FiltroConfig,
    manifesto_csv: Path,
    manifesto_metadata_json: Path,
    coberturas_mascara: dict[str, float] | None = None,
    modo_escrita: str = "w",
) -> list[tuple[str, Path]]:
    """Aplica o filtro unificado a todos os crops de `crops_dir` (uma fonte
    por vez), grava o manifesto de extração com hash, e retorna a lista de
    crops mantidos no formato (fonte, caminho) esperado por
    src.compose.compor_dataset.

    coberturas_mascara: dict opcional {nome_do_arquivo: cobertura} -- se
    None, o filtro roda sem checagem de máscara para todos os crops desta
    fonte (equivalente a `cobertura_mascara=None` por crop).

    modo_escrita: "w" (novo manifesto) ou "a" (acrescentar a um manifesto
    existente -- útil para rodar fonte por fonte e consolidar um único CSV).
    """
    crops_dir = Path(crops_dir)
    manifesto_csv = Path(manifesto_csv)
    manifesto_csv.parent.mkdir(parents=True, exist_ok=True)
    coberturas_mascara = coberturas_mascara or {}

    run_id = datetime.now(timezone.utc).strftime("extracao_%Y%m%dT%H%M%SZ")
    inicio = datetime.now(timezone.utc)

    arquivos = sorted(
        p for p in crops_dir.iterdir()
        if p.is_file() and p.suffix.lower() in _EXTENSOES_IMAGEM
    )

    escrever_cabecalho = modo_escrita == "w" or not manifesto_csv.exists()
    mantidos: list[tuple[str, Path]] = []
    n_avaliados = 0
    n_mantidos = 0

    with open(manifesto_csv, modo_escrita, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_FIELDNAMES)
        if escrever_cabecalho:
            writer.writeheader()

        for caminho in arquivos:
            n_avaliados += 1
            with Image.open(caminho) as img:
                largura, altura = img.size

            cobertura = coberturas_mascara.get(caminho.name)
            resultado = avaliar_crop(largura, altura, config, cobertura_mascara=cobertura)

            sha = _sha256_arquivo(caminho) if resultado.mantido else ""

            writer.writerow(asdict(LinhaManifestoExtracao(
                manifest_version=MANIFEST_EXTRACAO_VERSION,
                run_id=run_id,
                timestamp_avaliacao=datetime.now(timezone.utc).isoformat(),
                fonte=fonte,
                caminho_crop=str(caminho),
                largura_px=largura,
                altura_px=altura,
                cobertura_mascara="" if cobertura is None else f"{cobertura:.4f}",
                mantido=resultado.mantido,
                motivo=resultado.motivo,
                sha256=sha,
            )))

            if resultado.mantido:
                mantidos.append((fonte, caminho))
                n_mantidos += 1

    fim = datetime.now(timezone.utc)
    metadata = {
        "manifest_version": MANIFEST_EXTRACAO_VERSION,
        "run_id": run_id,
        "fonte": fonte,
        "config_filtro": asdict(config),
        "n_avaliados": n_avaliados,
        "n_mantidos": n_mantidos,
        "taxa_aproveitamento": (n_mantidos / n_avaliados) if n_avaliados else 0.0,
        "inicio_utc": inicio.isoformat(),
        "fim_utc": fim.isoformat(),
    }
    manifesto_metadata_json = Path(manifesto_metadata_json)
    manifesto_metadata_json.parent.mkdir(parents=True, exist_ok=True)
    # metadata por fonte -- se já existir (modo "a" entre fontes), acumula numa lista
    if manifesto_metadata_json.exists() and modo_escrita == "a":
        historico = json.loads(manifesto_metadata_json.read_text(encoding="utf-8"))
        if not isinstance(historico, list):
            historico = [historico]
        historico.append(metadata)
        manifesto_metadata_json.write_text(json.dumps(historico, indent=2, ensure_ascii=False), encoding="utf-8")
    else:
        manifesto_metadata_json.write_text(json.dumps([metadata], indent=2, ensure_ascii=False), encoding="utf-8")

    return mantidos

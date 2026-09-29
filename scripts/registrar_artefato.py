"""
Registra o SHA-256 de um ARTEFATO pré-treino em `docs/pre_registro/hashes.json`
(seção `artefatos`), sem alterar nenhuma entrada existente.

Uso na Fase 5 (adendo 3 §4.3): o manifesto da amostra sintética precisa
ter o hash registrado e commitado ANTES do primeiro treino.

    python scripts/registrar_artefato.py configs/amostra_sinteticas_fase5.csv

Salvaguardas (mesmas de lacrar_adendo.py):
- recusa registrar um nome que já existe (um artefato não é re-registrado;
  uma amostra nova exige um adendo novo);
- nunca sobrescreve `adendos` nem outros `artefatos`.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
HASHES = RAIZ / "docs" / "pre_registro" / "hashes.json"


def _sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(65536), b""):
            h.update(bloco)
    return h.hexdigest()


def _caminho_relativo(caminho: Path) -> str:
    try:
        return str(caminho.resolve().relative_to(RAIZ))
    except ValueError:
        return str(caminho)


def registrar_artefato(caminho: Path, hashes_json: Path = HASHES, nome: str | None = None) -> dict:
    caminho = Path(caminho)
    if not caminho.is_file():
        raise FileNotFoundError(f"Artefato não encontrado: {caminho}")
    nome = nome or caminho.name
    registro = json.loads(hashes_json.read_text(encoding="utf-8")) if hashes_json.exists() else {}
    registro.setdefault("artefatos", {})
    if nome in registro["artefatos"]:
        raise ValueError(f"'{nome}' já está registrado; uma amostra nova exige adendo novo, não re-registro.")
    registro["artefatos"][nome] = {
        "encontrado": True,
        "registrado_em_utc": datetime.now(timezone.utc).isoformat(),
        "caminho": _caminho_relativo(caminho),
        "sha256": _sha256(caminho),
        "tamanho_bytes": caminho.stat().st_size,
    }
    hashes_json.write_text(json.dumps(registro, indent=2, ensure_ascii=False), encoding="utf-8")
    return registro["artefatos"][nome]


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("uso: python scripts/registrar_artefato.py <caminho_do_artefato>")
        sys.exit(2)
    entrada = registrar_artefato(Path(sys.argv[1]))
    print(f"✅ Artefato registrado: {entrada['caminho']}")
    print(f"   sha256: {entrada['sha256']}")
    print("Agora commite hashes.json junto com o artefato -- ANTES de qualquer treino.")

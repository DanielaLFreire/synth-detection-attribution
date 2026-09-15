"""
Lacra um ADENDO ao pré-registro: calcula o SHA-256 do adendo e acrescenta
uma entrada em `docs/pre_registro/hashes.json` SEM alterar nenhuma entrada
existente. Registra também o hash atual de `previsoes_fase0.md` como prova
cruzada de que o original não foi editado.

Salvaguardas:
- Recusa lacrar se o adendo ainda contém o marcador de decisão pendente
  ("DECISÃO PENDENTE" ou "___").
- Recusa lacrar se já existe uma entrada com o mesmo nome (um adendo não
  é re-lacrado; correções vão em novo adendo).
- Nunca sobrescreve `artefatos` existentes -- só acrescenta em `adendos`.

Uso (local ou Colab, só precisa do repositório):

    python scripts/lacrar_adendo.py docs/pre_registro/adendo_fase3_fatorial.md
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
HASHES = RAIZ / "docs" / "pre_registro" / "hashes.json"
ORIGINAL = RAIZ / "docs" / "pre_registro" / "previsoes_fase0.md"
MARCADORES_PENDENTES = ("DECISÃO PENDENTE", "___")


def _caminho_relativo(caminho: Path) -> str:
    try:
        return str(caminho.resolve().relative_to(RAIZ))
    except ValueError:
        return str(caminho)


def _sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(65536), b""):
            h.update(bloco)
    return h.hexdigest()


def lacrar_adendo(caminho_adendo: Path, hashes_json: Path = HASHES, original: Path = ORIGINAL) -> dict:
    caminho_adendo = Path(caminho_adendo)
    texto = caminho_adendo.read_text(encoding="utf-8")
    for marcador in MARCADORES_PENDENTES:
        if marcador in texto:
            raise ValueError(f"Adendo contém '{marcador}': resolva a decisão pendente antes de lacrar.")

    registro = json.loads(hashes_json.read_text(encoding="utf-8")) if hashes_json.exists() else {"artefatos": {}}
    registro.setdefault("adendos", {})
    nome = caminho_adendo.name
    if nome in registro["adendos"]:
        raise ValueError(f"'{nome}' já está lacrado; correções vão em um novo adendo, não em re-lacração.")

    registro["adendos"][nome] = {
        "lacrado_em_utc": datetime.now(timezone.utc).isoformat(),
        "caminho": _caminho_relativo(caminho_adendo),
        "sha256": _sha256(caminho_adendo),
        "tamanho_bytes": caminho_adendo.stat().st_size,
        "sha256_previsoes_fase0_md_no_momento": _sha256(original) if original.exists() else None,
    }
    hashes_json.write_text(json.dumps(registro, indent=2, ensure_ascii=False), encoding="utf-8")
    return registro["adendos"][nome]


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("uso: python scripts/lacrar_adendo.py <caminho_do_adendo.md>")
        sys.exit(2)
    entrada = lacrar_adendo(Path(sys.argv[1]))
    print(f"✅ Adendo lacrado: {entrada['caminho']}")
    print(f"   sha256: {entrada['sha256']}")
    print(f"   previsoes_fase0.md (prova cruzada): {entrada['sha256_previsoes_fase0_md_no_momento']}")
    print("Agora commite hashes.json junto com o adendo -- o commit público é a lacração.")

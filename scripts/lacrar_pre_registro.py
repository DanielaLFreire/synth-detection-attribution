"""
Script de entrada para a tarefa 0.6: calcula o hash SHA-256 de cada
artefato citado no documento de previsões pré-registradas
(docs/pre_registro/previsoes_fase0.md), e grava em
`pre_registro/hashes.json` -- tanto no Drive quanto (via cópia manual, ver
instruções) no repositório, para que o commit de lacração inclua a prova
de integridade junto com as previsões.

Uso no Colab:

    import sys
    sys.path.insert(0, "/content/synth-detection-attribution")
    from scripts.lacrar_pre_registro import main

    main()
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

RAIZ_PRE_REGISTRO = "/content/drive/MyDrive/PROJETO_MARINHA/EXPERIMENTO_ATRIBUICAO_CAUSAL/pre_registro"
RAIZ_ESTAGIO_A = "/content/drive/MyDrive/PROJETO_MARINHA/EXPERIMENTO_ATRIBUICAO_CAUSAL/estagio_a/colagens_sondagem_val"

ARTEFATOS_PADRAO = {
    "perfil_citra_3d_real.json": f"{RAIZ_PRE_REGISTRO}/perfil_citra_3d_real.json",
    "tabela_min_dim_px.json": f"{RAIZ_PRE_REGISTRO}/tabela_min_dim_px.json",
    "cobertura_fatorial.json": f"{RAIZ_PRE_REGISTRO}/cobertura_fatorial.json",
    "manifesto_colagens_sondagem_val.csv": f"{RAIZ_ESTAGIO_A}/manifesto_colagens_sondagem_val.csv",
}


def _sha256_arquivo(caminho: Path) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(65536), b""):
            h.update(bloco)
    return h.hexdigest()


def main(
    artefatos: dict[str, str] | None = None,
    destino_json: str = f"{RAIZ_PRE_REGISTRO}/hashes.json",
) -> dict:
    artefatos = artefatos or ARTEFATOS_PADRAO
    registro = {
        "gerado_em_utc": datetime.now(timezone.utc).isoformat(),
        "artefatos": {},
    }

    print("Calculando hashes dos artefatos citados no pré-registro...\n")
    for nome, caminho in artefatos.items():
        caminho_path = Path(caminho)
        if not caminho_path.exists():
            print(f"  ⚠️  {nome}: NÃO ENCONTRADO em {caminho} -- pulado.")
            registro["artefatos"][nome] = {"encontrado": False, "caminho": caminho}
            continue
        sha = _sha256_arquivo(caminho_path)
        tamanho = caminho_path.stat().st_size
        registro["artefatos"][nome] = {
            "encontrado": True, "caminho": caminho, "sha256": sha, "tamanho_bytes": tamanho,
        }
        print(f"  ✅ {nome}: {sha[:16]}... ({tamanho:,} bytes)")

    destino_path = Path(destino_json)
    destino_path.parent.mkdir(parents=True, exist_ok=True)
    destino_path.write_text(json.dumps(registro, indent=2, ensure_ascii=False), encoding="utf-8")

    n_faltando = sum(1 for a in registro["artefatos"].values() if not a["encontrado"])
    print(f"\n{'✅' if n_faltando == 0 else '⚠️ '} {len(artefatos) - n_faltando} de {len(artefatos)} "
          f"artefatos com hash registrado.")
    print(f"Resultado salvo em {destino_path}")

    if n_faltando > 0:
        print("\nATENÇÃO: nem todos os artefatos foram encontrados -- confira os caminhos "
              "antes de considerar o pré-registro lacrado.")

    return registro


if __name__ == "__main__":
    main()

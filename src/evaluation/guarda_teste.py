"""
Trava de avaliação única do split de TESTE (§7 do plano: "nunca tocado
antes da Fase 4", avaliado uma única vez).

O marcador é gravado no Drive ao final da avaliação. Uma segunda chamada
é recusada com erro explícito. Não há flag para contornar: se algum dia
for necessário reavaliar, a decisão deve ser documentada num adendo e o
marcador removido à mão, deixando rastro.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


class AvaliacaoDeTesteJaRealizada(RuntimeError):
    pass


def verificar_avaliacao_unica(marcador: Path) -> None:
    marcador = Path(marcador)
    if marcador.exists():
        info = json.loads(marcador.read_text(encoding="utf-8"))
        raise AvaliacaoDeTesteJaRealizada(
            f"O split de teste já foi avaliado em {info.get('avaliado_em_utc')} "
            f"(commit {info.get('commit')}). Reavaliar exige adendo documentado.")


def registrar_avaliacao(marcador: Path, info: dict) -> dict:
    marcador = Path(marcador)
    marcador.parent.mkdir(parents=True, exist_ok=True)
    registro = {"avaliado_em_utc": datetime.now(timezone.utc).isoformat(), **info}
    marcador.write_text(json.dumps(registro, indent=2, ensure_ascii=False), encoding="utf-8")
    return registro

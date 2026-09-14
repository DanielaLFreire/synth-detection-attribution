"""
Script de entrada para a Fase 2 (Estágio A): constrói o alvo binário a
partir do manifesto de composição e das detecções brutas dos 3
checkpoints de B2 -- tudo em CPU, nenhuma GPU envolvida.

Uso no Colab:

    import sys
    sys.path.insert(0, "/content/synth-detection-attribution")
    from scripts.construir_alvo_estagio_a import main

    main()
"""
from __future__ import annotations

import json
from pathlib import Path

from src.attribution import construir_alvo

DRIVE_SONDAGEM = "/content/drive/MyDrive/PROJETO_MARINHA/EXPERIMENTO_ATRIBUICAO_CAUSAL/estagio_a/colagens_sondagem_val"
DRIVE_DETECCOES = "/content/drive/MyDrive/PROJETO_MARINHA/EXPERIMENTO_ATRIBUICAO_CAUSAL/estagio_a/deteccoes_brutas"
DRIVE_ALVO = "/content/drive/MyDrive/PROJETO_MARINHA/EXPERIMENTO_ATRIBUICAO_CAUSAL/estagio_a/alvo"

SEEDS_B2 = [42, 123, 2024]


def main(
    iou_min: float = 0.5,
    conf_min: float = 0.25,
    drive_sondagem: str = DRIVE_SONDAGEM,
    drive_deteccoes: str = DRIVE_DETECCOES,
    drive_alvo: str = DRIVE_ALVO,
    seeds: list[int] | None = None,
) -> dict:
    seeds = seeds or SEEDS_B2
    manifesto = Path(drive_sondagem) / "manifesto_colagens_sondagem_val.csv"
    deteccoes = {s: Path(drive_deteccoes) / f"deteccoes_B2_seed{s}.csv" for s in seeds}
    destino = Path(drive_alvo) / f"alvo_iou{iou_min}_conf{conf_min}.csv"

    print(f"Construindo alvo (iou_min={iou_min}, conf_min={conf_min}, seeds={seeds})...")
    resumo = construir_alvo(manifesto, deteccoes, destino, iou_min=iou_min, conf_min=conf_min)

    print(f"\n  Caixas coladas processadas: {resumo['n_caixas']}")
    for s, taxa in resumo["taxa_acerto_por_seed"].items():
        print(f"  Taxa de acerto seed {s}: {taxa:.3f}")
    print(f"  Taxa de acerto por VOTAÇÃO (maioria de {len(seeds)}): {resumo['taxa_acerto_votacao']:.3f}")

    Path(drive_alvo).mkdir(parents=True, exist_ok=True)
    (Path(drive_alvo) / f"resumo_alvo_iou{iou_min}_conf{conf_min}.json").write_text(
        json.dumps(resumo, indent=2, ensure_ascii=False), encoding="utf-8",
    )
    print(f"\n✅ Alvo salvo em {destino}")
    return resumo


if __name__ == "__main__":
    main()

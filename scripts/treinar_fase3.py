"""
Fase 3 -- treino retomável do fatorial 2 × 2 (adendo 2, commit a4ec7ab).
GPU. ~1,5 h por execução; 15 execuções (4 células + controle) × 3 seeds.

`main()` verifica no Drive o que já terminou (150 épocas + last.pt) e roda
SÓ o que falta, em ordem fixa. Pode ser chamado quantas vezes for
preciso, em sessões diferentes -- só a execução em andamento se perde
numa desconexão. `listar()` mostra o estado sem treinar nada.

Uso no Colab (GPU):

    import sys
    sys.path.insert(0, "/content/synth-detection-attribution")
    from scripts.treinar_fase3 import listar, main

    listar()          # estado
    main()            # roda as pendentes, em ordem
    main(max_execucoes=2)   # ou só algumas por sessão
"""
from __future__ import annotations

import json
from pathlib import Path

from src.train import Execucao, execucoes_pendentes, execucao_concluida, treinar_execucao

DADOS_LOCAIS = "/content/fase3_dados_locais"
DESTINO_RUNS = "/content/fase3_runs"
DESTINO_RUNS_DRIVE = "/content/drive/MyDrive/PROJETO_MARINHA/EXPERIMENTO_ATRIBUICAO_CAUSAL/fase3/runs"
BRACOS = ["casada__alto", "casada__baixo", "reduzida__alto", "reduzida__baixo", "controle"]
SEEDS = [42, 123, 2024]
EPOCHS_TOTAL = 150  # epoca_checkpoint = 150, fechado na Fase 1

# ordem fixa: seed externa, braço interno -- assim, a cada 5 execuções, todos os
# braços têm a mesma seed completa (uma "réplica" inteira analisável)
PLANEJADAS = [Execucao(b, s) for s in SEEDS for b in BRACOS]


def listar(destino_runs_drive: str = DESTINO_RUNS_DRIVE) -> list[Execucao]:
    pend = execucoes_pendentes(PLANEJADAS, Path(destino_runs_drive), EPOCHS_TOTAL)
    print(f"Planejadas: {len(PLANEJADAS)} | concluídas: {len(PLANEJADAS) - len(pend)} | pendentes: {len(pend)}")
    for e in PLANEJADAS:
        ok = execucao_concluida(Path(destino_runs_drive) / e.nome, EPOCHS_TOTAL)
        print(f"  {'✅' if ok else '⏳'} {e.nome}")
    return pend


def main(max_execucoes: int | None = None, dados_locais: str = DADOS_LOCAIS, destino_runs: str = DESTINO_RUNS,
         destino_runs_drive: str = DESTINO_RUNS_DRIVE) -> list[str]:
    contagens = json.loads((Path(dados_locais) / "configs" / "contagens.json").read_text(encoding="utf-8"))["n_imagens_epoca"]
    pend = listar(destino_runs_drive)
    if max_execucoes is not None:
        pend = pend[:max_execucoes]
    feitas = []
    for e in pend:
        print(f"\n=== Treinando {e.nome} ({contagens[e.braco]} imgs/época) ===")
        treinar_execucao(
            e, n_imagens_epoca=contagens[e.braco],
            data_yaml=Path(dados_locais) / "configs" / f"data_{e.braco}.yaml",
            destino_runs=Path(destino_runs), destino_runs_drive=Path(destino_runs_drive),
            epochs_total=EPOCHS_TOTAL,
        )
        assert execucao_concluida(Path(destino_runs_drive) / e.nome, EPOCHS_TOTAL), f"{e.nome} terminou mas não passou na verificação"
        feitas.append(e.nome)
    print(f"\nConcluídas nesta sessão: {feitas}")
    listar(destino_runs_drive)
    return feitas


if __name__ == "__main__":
    main()

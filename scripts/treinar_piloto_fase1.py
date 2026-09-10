"""
Script de entrada para a Fase 1: invoca o treino Ultralytics YOLO para os
três braços (B2, A_joint, controle) da piloto do protocolo V2.

`epoca_checkpoint` usado aqui é um PLACEHOLDER (última época) -- a piloto
existe justamente para descobrir o valor real, observando onde a curva de
validação atinge o pico antes de degradar (padrão já documentado no
projeto anterior para braços com sintético: pico muito precoce, seguido de
degradação lenta -- ver docs/CHANGELOG_metodologico.md, 2026-09-02). O
valor usado aqui não deve ser tratado como decisão final do protocolo.

Uso no Colab (GPU necessária a partir daqui):

    import sys
    sys.path.insert(0, "/content/synth-detection-attribution")
    from scripts.treinar_piloto_fase1 import treinar_um_braco, main

    main()  # roda os 3 braços x 3 seeds (9 treinos)
"""
from __future__ import annotations

from pathlib import Path
import shutil

from src.train import ProtocoloTreinoV2, gerar_kwargs_treino

DADOS_LOCAIS = "/content/fase1_dados_locais"
DESTINO_RUNS = "/content/fase1_runs"
DESTINO_RUNS_DRIVE = "/content/drive/MyDrive/PROJETO_MARINHA/EXPERIMENTO_ATRIBUICAO_CAUSAL/fase1_piloto/runs"

# Contagens de imagens por época, já confirmadas na preparação dos dados
N_IMAGENS_EPOCA = {
    "B2": 1348,
    "A_joint": 35048,
    "controle": 17524,
}

SEEDS_PILOTO = [42, 123, 2024]

EPOCHS_TOTAL_PILOTO = 150  # proposto e justificado; ver conversa/changelog -- ajustável


def treinar_um_braco(
    nome_braco: str,
    seed: int,
    epochs_total: int = EPOCHS_TOTAL_PILOTO,
    dados_locais: str = DADOS_LOCAIS,
    destino_runs: str = DESTINO_RUNS,
    destino_runs_drive: str = DESTINO_RUNS_DRIVE,
    pesos_base: str = "yolo11n.pt",
):
    """Roda um único treino (um braço, uma seed). Retorna o objeto de
    resultados do Ultralytics.

    CORREÇÃO 2026-09-09: copia results.csv + args.yaml + weights/*.pt para
    o Drive ao final -- antes desta correção, os resultados ficavam só em
    `/content/...` (local do Colab), vulnerável a perda completa em caso
    de desconexão de sessão (o que já aconteceu uma vez, ver
    docs/CHANGELOG_metodologico.md). Os dados dos seeds 42/123/2024 do
    braço B2 já treinados antes desta correção não foram salvos no Drive
    -- só recuperados via log de console colado na conversa.
    """
    from ultralytics import YOLO  # import tardio -- só necessário com GPU

    protocolo = ProtocoloTreinoV2(
        pesos_base=pesos_base,
        epochs_total=epochs_total,
        epoca_checkpoint=epochs_total,  # PLACEHOLDER -- ver docstring do módulo
        warmup_steps_alvo=500,
        batch_size=16,
    )

    kwargs = gerar_kwargs_treino(
        protocolo,
        n_imagens_epoca_deste_braco=N_IMAGENS_EPOCA[nome_braco],
        nome_braco=nome_braco,
        seed=seed,
    )

    model_path = kwargs.pop("model")
    kwargs.pop("_epoca_checkpoint_a_usar")  # não é argumento de .train(); placeholder mesmo

    data_yaml = Path(dados_locais) / "configs" / f"data_{nome_braco}.yaml"
    if not data_yaml.exists():
        raise FileNotFoundError(f"data.yaml não encontrado em {data_yaml} -- rode "
                                 "preparar_dados_locais_fase1.py primeiro.")

    model = YOLO(model_path)
    resultados = model.train(
        data=str(data_yaml),
        project=destino_runs,
        deterministic=True,  # exigido para o portão de determinismo (§9 do plano)
        **kwargs,
    )

    # cópia para o Drive -- ver docstring, correção de 2026-09-09
    pasta_run_local = Path(destino_runs) / kwargs["name"]
    pasta_run_drive = Path(destino_runs_drive) / kwargs["name"]
    pasta_run_drive.mkdir(parents=True, exist_ok=True)
    for nome_arquivo in ("results.csv", "args.yaml"):
        origem = pasta_run_local / nome_arquivo
        if origem.exists():
            shutil.copy2(origem, pasta_run_drive / nome_arquivo)
    pasta_weights_drive = pasta_run_drive / "weights"
    pasta_weights_drive.mkdir(parents=True, exist_ok=True)
    for nome_peso in ("best.pt", "last.pt"):
        origem = pasta_run_local / "weights" / nome_peso
        if origem.exists():
            shutil.copy2(origem, pasta_weights_drive / nome_peso)
    print(f"   Resultados copiados para o Drive: {pasta_run_drive}")

    return resultados


def main(
    bracos: list[str] | None = None,
    seeds: list[int] | None = None,
    epochs_total: int = EPOCHS_TOTAL_PILOTO,
) -> None:
    bracos = bracos or ["B2", "A_joint", "controle"]
    seeds = seeds or SEEDS_PILOTO

    for nome_braco in bracos:
        for seed in seeds:
            print(f"\n{'='*70}\nTreinando: {nome_braco}, seed={seed}, epochs_total={epochs_total}\n{'='*70}")
            treinar_um_braco(nome_braco, seed, epochs_total=epochs_total)


if __name__ == "__main__":
    main()

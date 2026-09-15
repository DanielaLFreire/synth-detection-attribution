"""
Executor de treino retomável (Fase 3; reaproveitável na Fase 4).

Lições da Fase 1 incorporadas:
- Resultados copiados para o Drive ao final de CADA execução
  (results.csv, args.yaml, weights/*.pt) -- desconexão só perde a
  execução em andamento.
- Conclusão verificada com rigor: `results.csv` com `epochs_total` linhas
  E `weights/last.pt` presente. A existência do arquivo não basta (um
  treino interrompido também gera um results.csv parcial).
- Contagem de imagens por época lida de arquivo gerado na preparação dos
  dados, nunca codificada à mão.
- `epoca_checkpoint = epochs_total` (decisão fechada na Fase 1).
"""
from __future__ import annotations

import csv
import shutil
from dataclasses import dataclass
from pathlib import Path

from .protocol import ProtocoloTreinoV2, gerar_kwargs_treino


@dataclass(frozen=True)
class Execucao:
    braco: str
    seed: int

    @property
    def nome(self) -> str:
        return f"{self.braco}_seed{self.seed}"


def execucao_concluida(pasta_run_drive: Path, epochs_total: int) -> bool:
    """True só se results.csv tem exatamente `epochs_total` épocas E last.pt existe."""
    csv_path = Path(pasta_run_drive) / "results.csv"
    last = Path(pasta_run_drive) / "weights" / "last.pt"
    if not (csv_path.exists() and last.exists()):
        return False
    with open(csv_path, newline="", encoding="utf-8") as f:
        linhas = list(csv.DictReader(f))
    if len(linhas) != epochs_total:
        return False
    try:
        return int(float(linhas[-1]["epoch"])) == epochs_total
    except (KeyError, ValueError):
        return False


def execucoes_pendentes(planejadas: list[Execucao], destino_runs_drive: Path, epochs_total: int) -> list[Execucao]:
    return [e for e in planejadas if not execucao_concluida(Path(destino_runs_drive) / e.nome, epochs_total)]


def copiar_resultados_para_drive(pasta_run_local: Path, pasta_run_drive: Path) -> None:
    pasta_run_drive.mkdir(parents=True, exist_ok=True)
    for nome in ("results.csv", "args.yaml"):
        origem = Path(pasta_run_local) / nome
        if origem.exists():
            shutil.copy2(origem, pasta_run_drive / nome)
    (pasta_run_drive / "weights").mkdir(parents=True, exist_ok=True)
    for nome in ("best.pt", "last.pt"):
        origem = Path(pasta_run_local) / "weights" / nome
        if origem.exists():
            shutil.copy2(origem, pasta_run_drive / "weights" / nome)


def treinar_execucao(
    execucao: Execucao,
    n_imagens_epoca: int,
    data_yaml: Path,
    destino_runs: Path,
    destino_runs_drive: Path,
    epochs_total: int = 150,
    pesos_base: str = "yolo11n.pt",
    warmup_steps_alvo: int = 500,
    batch_size: int = 16,
):
    """Uma execução (braço, seed) com o protocolo V2; copia para o Drive ao final."""
    from ultralytics import YOLO  # import tardio -- GPU

    if not Path(data_yaml).exists():
        raise FileNotFoundError(f"data.yaml não encontrado: {data_yaml}")

    protocolo = ProtocoloTreinoV2(
        pesos_base=pesos_base, epochs_total=epochs_total, epoca_checkpoint=epochs_total,
        warmup_steps_alvo=warmup_steps_alvo, batch_size=batch_size,
    )
    kwargs = gerar_kwargs_treino(protocolo, n_imagens_epoca_deste_braco=n_imagens_epoca,
                                 nome_braco=execucao.braco, seed=execucao.seed)
    model_path = kwargs.pop("model")
    kwargs.pop("_epoca_checkpoint_a_usar")
    kwargs["name"] = execucao.nome

    model = YOLO(model_path)
    resultados = model.train(data=str(data_yaml), project=str(destino_runs), deterministic=True, exist_ok=True, **kwargs)

    copiar_resultados_para_drive(Path(destino_runs) / execucao.nome, Path(destino_runs_drive) / execucao.nome)
    return resultados

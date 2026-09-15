"""Testes do executor retomável (lógica de conclusão e pendências)."""
from __future__ import annotations

from pathlib import Path

from src.train import Execucao, execucao_concluida, execucoes_pendentes, copiar_resultados_para_drive


def _run(pasta: Path, n_epocas: int, com_last: bool = True, epoch_final: int | None = None):
    pasta.mkdir(parents=True, exist_ok=True)
    linhas = ["epoch,metrics/recall(B)"] + [f"{i},0.7" for i in range(1, n_epocas + 1)]
    if epoch_final is not None and n_epocas:
        linhas[-1] = f"{epoch_final},0.7"
    (pasta / "results.csv").write_text("\n".join(linhas) + "\n")
    if com_last:
        (pasta / "weights").mkdir(exist_ok=True)
        (pasta / "weights" / "last.pt").write_bytes(b"x")


def test_concluida_exige_todas_as_epocas_e_last(tmp_path):
    _run(tmp_path / "ok", 150)
    assert execucao_concluida(tmp_path / "ok", 150)


def test_parcial_nao_e_concluida(tmp_path):
    _run(tmp_path / "parcial", 80)
    assert not execucao_concluida(tmp_path / "parcial", 150)


def test_sem_last_nao_e_concluida(tmp_path):
    _run(tmp_path / "semlast", 150, com_last=False)
    assert not execucao_concluida(tmp_path / "semlast", 150)


def test_epoca_final_errada_nao_e_concluida(tmp_path):
    _run(tmp_path / "estranho", 150, epoch_final=149)  # 150 linhas mas a última não é a época 150
    assert not execucao_concluida(tmp_path / "estranho", 150)


def test_pasta_inexistente_nao_e_concluida(tmp_path):
    assert not execucao_concluida(tmp_path / "nada", 150)


def test_pendentes_filtra_as_concluidas(tmp_path):
    planejadas = [Execucao("A", 42), Execucao("A", 123), Execucao("B", 42)]
    _run(tmp_path / "A_seed42", 150)
    _run(tmp_path / "B_seed42", 30)  # parcial
    pend = execucoes_pendentes(planejadas, tmp_path, 150)
    assert [e.nome for e in pend] == ["A_seed123", "B_seed42"]


def test_copiar_resultados_leva_csv_args_e_pesos(tmp_path):
    local = tmp_path / "local"; _run(local, 3)
    (local / "args.yaml").write_text("a: 1")
    (local / "weights" / "best.pt").write_bytes(b"y")
    drive = tmp_path / "drive"
    copiar_resultados_para_drive(local, drive)
    for f in ("results.csv", "args.yaml", "weights/last.pt", "weights/best.pt"):
        assert (drive / f).exists(), f

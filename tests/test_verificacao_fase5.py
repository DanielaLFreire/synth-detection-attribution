"""Fase 5, G2/G3 (adendo 3 §8): comparação de results.csv, contagem real
de passos por callback, pré-requisitos e trava do portão -- tudo em CPU."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.train.passos_fixos import ExecucaoF5, execucoes_portao_g2
from src.train.verificacao_fase5 import (
    NOME_JSON_PASSOS, ContadorPassos, comparar_results_csv, verificar_passos,
    verificar_pre_requisitos, veredito_g2,
)

CAB = "epoch,time,train/box_loss,metrics/recall(B),lr/pg0"


def _results(p: Path, linhas: list[str], cab: str = CAB) -> Path:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(cab + "\n" + "\n".join(linhas) + "\n", encoding="utf-8")
    return p


BASE = ["1,30.1,2.0,0.15,0.0001", "2,60.2,1.8,0.49,0.0002"]


# --- G2: comparação de results.csv ---

def test_identico_exceto_tempo_passa(tmp_path):
    a = _results(tmp_path / "a.csv", BASE)
    b = _results(tmp_path / "b.csv", ["1,31.7,2.0,0.15,0.0001", "2,63.0,1.8,0.49,0.0002"])
    r = comparar_results_csv(a, b)
    assert r.identico and "time" not in r.colunas_comparadas


def test_menor_diferenca_numerica_reprova(tmp_path):
    a = _results(tmp_path / "a.csv", BASE)
    b = _results(tmp_path / "b.csv", ["1,30.1,2.0,0.15,0.0001", "2,60.2,1.8,0.4900001,0.0002"])
    r = comparar_results_csv(a, b)
    assert not r.identico
    assert r.divergencias["metrics/recall(B)"]["primeira_epoca"] == "2"
    assert r.divergencias["metrics/recall(B)"]["max_abs_diff"] == pytest.approx(1e-7)


def test_numero_de_epocas_diferente_reprova(tmp_path):
    a = _results(tmp_path / "a.csv", BASE)
    b = _results(tmp_path / "b.csv", BASE[:1])
    assert not comparar_results_csv(a, b).identico


def test_cabecalho_com_espacos_e_normalizado(tmp_path):
    a = _results(tmp_path / "a.csv", BASE)
    b = _results(tmp_path / "b.csv", BASE, cab="  epoch,  time, train/box_loss,metrics/recall(B),lr/pg0")
    assert comparar_results_csv(a, b).identico


def test_nan_igual_a_nan(tmp_path):
    a = _results(tmp_path / "a.csv", ["1,1,nan,0.1,0.1"])
    b = _results(tmp_path / "b.csv", ["1,2,nan,0.1,0.1"])
    assert comparar_results_csv(a, b).identico


# --- G3: contagem real de passos ---

class _Loader:
    def __init__(self, n_imgs, nb):
        self.dataset, self._nb = list(range(n_imgs)), nb

    def __len__(self):
        return self._nb


def _trainer(n_imgs=5392, nb=337, epochs=30, close_mosaic=2):
    loader = _Loader(n_imgs, nb)
    return SimpleNamespace(train_loader=loader, epochs=epochs, batch_size=16,
                           args=SimpleNamespace(close_mosaic=close_mosaic, warmup_epochs=500 / 337, seed=42))


def _simular(tmp_path, n_passos, **kw) -> Path:
    destino = tmp_path / NOME_JSON_PASSOS
    c, t = ContadorPassos(destino), _trainer(**kw)
    c.on_train_start(t)
    for _ in range(n_passos):
        c.on_train_batch_end(t)
    c.on_train_end(t)
    return destino


def test_contador_registra_e_callbacks_sao_adicionados(tmp_path):
    registrados = []
    modelo = SimpleNamespace(add_callback=lambda ev, fn: registrados.append(ev))
    ContadorPassos(tmp_path / "x.json").registrar(modelo)
    assert registrados == ["on_train_start", "on_train_batch_end", "on_train_end"]
    dados = json.loads(_simular(tmp_path, 10110).read_text())
    assert dados["passos_executados"] == 10110 and dados["n_imagens_dataset"] == 5392 and dados["passos_por_epoca"] == 337


def test_passos_corretos_s1_aprovam(tmp_path):
    assert verificar_passos(_simular(tmp_path, 10110), "S1") == []


def test_passos_s2_aprovam(tmp_path):
    assert verificar_passos(_simular(tmp_path, 25275, epochs=75, close_mosaic=5), "S2") == []


def test_passo_a_menos_reprova(tmp_path):
    assert any("passos_executados" in p for p in verificar_passos(_simular(tmp_path, 10109), "S1"))


def test_dataset_deduplicado_reprova(tmp_path):
    """Se o treinador deduplicasse as linhas repetidas da trainlist, o
    dataset teria 1.348 imagens e 85 passos/época -- G3 deve pegar."""
    p = verificar_passos(_simular(tmp_path, 30 * 85, n_imgs=1348, nb=85), "S1")
    assert any("n_imagens_dataset" in x for x in p) and any("passos_por_epoca" in x for x in p)


def test_close_mosaic_errado_reprova(tmp_path):
    assert any("close_mosaic" in p for p in verificar_passos(_simular(tmp_path, 10110, close_mosaic=10), "S1"))


def test_json_ausente_reprova(tmp_path):
    assert verificar_passos(tmp_path / NOME_JSON_PASSOS, "S1") == [f"{NOME_JSON_PASSOS} ausente"]


# --- veredito G2 ---

def test_veredito_go(tmp_path):
    a = _results(tmp_path / "a/results.csv", BASE)
    b = _results(tmp_path / "b/results.csv", BASE)
    ja, jb = _simular(tmp_path / "a", 10110), _simular(tmp_path / "b", 10110)
    assert veredito_g2(a, b, ja, jb)["veredito"] == "GO"


def test_veredito_no_go_por_metrica(tmp_path):
    a = _results(tmp_path / "a/results.csv", BASE)
    b = _results(tmp_path / "b/results.csv", ["1,30.1,2.0,0.15,0.0001", "2,60.2,1.8,0.50,0.0002"])
    ja, jb = _simular(tmp_path / "a", 10110), _simular(tmp_path / "b", 10110)
    assert veredito_g2(a, b, ja, jb)["veredito"] == "NO-GO"


def test_veredito_no_go_por_passos(tmp_path):
    a = _results(tmp_path / "a/results.csv", BASE)
    b = _results(tmp_path / "b/results.csv", BASE)
    ja, jb = _simular(tmp_path / "a", 10110), _simular(tmp_path / "b", 10000)
    assert veredito_g2(a, b, ja, jb)["veredito"] == "NO-GO"


# --- pré-requisitos ---

def _repo_e_dados(tmp_path, adulterar=False, registrar=True):
    repo, dados = tmp_path / "repo", tmp_path / "dados"
    (repo / "configs").mkdir(parents=True)
    (repo / "docs/pre_registro").mkdir(parents=True)
    man = repo / "configs/amostra_sinteticas_fase5.csv"
    man.write_text("ordem,celula\n", encoding="utf-8")
    h = hashlib.sha256(man.read_bytes()).hexdigest()
    art = {"amostra_sinteticas_fase5.csv": {"sha256": h}} if registrar else {}
    (repo / "docs/pre_registro/hashes.json").write_text(json.dumps({"artefatos": art}), encoding="utf-8")
    if adulterar:
        man.write_text("ordem,celula\n0,x\n", encoding="utf-8")
    (dados / "configs").mkdir(parents=True)
    (dados / "configs/contagens_f5.json").write_text(
        json.dumps({b: {"n_total": 5392} for b in ("C", "M25", "M50")}), encoding="utf-8")
    for b in ("C", "M25", "M50"):
        (dados / f"configs/data_f5_{b}.yaml").write_text("x", encoding="utf-8")
    return repo, dados


def test_pre_requisitos_ok(tmp_path):
    assert verificar_pre_requisitos(*_repo_e_dados(tmp_path)) == []


def test_manifesto_adulterado_bloqueia(tmp_path):
    assert any("diverge" in p for p in verificar_pre_requisitos(*_repo_e_dados(tmp_path, adulterar=True)))


def test_manifesto_nao_registrado_bloqueia(tmp_path):
    assert any("não registrado" in p for p in verificar_pre_requisitos(*_repo_e_dados(tmp_path, registrar=False)))


# --- script: estados e trava do portão ---

def _run_drive(drive: Path, e: ExecucaoF5, epocas: int, passos: int, close_mosaic: int):
    pasta = drive / e.nome
    _results(pasta / "results.csv", [f"{i},1,1,0.5,0.1" for i in range(1, epocas + 1)])
    (pasta / "weights").mkdir(parents=True, exist_ok=True)
    (pasta / "weights/last.pt").write_bytes(b"x")
    (pasta / NOME_JSON_PASSOS).write_text(json.dumps({
        "n_imagens_dataset": 5392, "passos_por_epoca": 337, "epochs": epocas,
        "close_mosaic": close_mosaic, "passos_executados": passos}), encoding="utf-8")


def test_estado_concluida_pendente_violacao(tmp_path):
    from scripts.treinar_fase5 import estado
    e = ExecucaoF5("S1", "C", 42)
    assert estado(e, str(tmp_path)) == "pendente"
    _run_drive(tmp_path, e, 30, 10110, 2)
    assert estado(e, str(tmp_path)) == "concluida"
    _run_drive(tmp_path, e, 30, 9999, 2)
    assert estado(e, str(tmp_path)) == "violacao"


def test_main_recusa_sem_g2_go(tmp_path):
    from scripts.treinar_fase5 import PortaoNaoAprovado, main
    with pytest.raises(PortaoNaoAprovado):
        main(arquivo_g2=str(tmp_path / "portao_g2.json"), destino_runs_drive=str(tmp_path))
    (tmp_path / "portao_g2.json").write_text(json.dumps({"veredito": "NO-GO"}), encoding="utf-8")
    with pytest.raises(PortaoNaoAprovado):
        main(arquivo_g2=str(tmp_path / "portao_g2.json"), destino_runs_drive=str(tmp_path))


def test_g2_registrado_nao_e_reexecutado(tmp_path):
    from scripts.treinar_fase5 import portao_g2
    arq = tmp_path / "portao_g2.json"
    arq.write_text(json.dumps({"veredito": "GO", "registrado_em_utc": "x"}), encoding="utf-8")
    assert portao_g2(arquivo_g2=str(arq), dados_locais=str(tmp_path / "nao_existe"))["veredito"] == "GO"


def test_original_do_g2_conta_na_lista_fechada(tmp_path):
    """A 1ª execução do G2 é a própria f5_S1_C_seed42 do plano: depois do
    portão, main() não a treina de novo."""
    from scripts.treinar_fase5 import estado
    original, _ = execucoes_portao_g2()
    _run_drive(tmp_path, original, 30, 10110, 2)
    assert estado(ExecucaoF5("S1", "C", 42), str(tmp_path)) == "concluida"


def test_diferencas_de_ambiente():
    from scripts.treinar_fase5 import diferencas_ambiente
    reg = {"gpu": "NVIDIA A100-SXM4-40GB", "torch": "2.8.0", "ultralytics": "8.3.200"}
    assert diferencas_ambiente(reg, dict(reg)) == {}
    assert diferencas_ambiente(reg, {**reg, "gpu": "NVIDIA L4"}) == {"gpu": ("NVIDIA A100-SXM4-40GB", "NVIDIA L4")}


def test_main_bloqueia_ambiente_diferente(tmp_path, monkeypatch):
    import scripts.treinar_fase5 as t
    arq = tmp_path / "portao_g2.json"
    arq.write_text(json.dumps({"veredito": "GO", "ambiente": {"gpu": "A100", "torch": "2", "ultralytics": "8"}}), encoding="utf-8")
    monkeypatch.setattr(t, "_ambiente", lambda: {"gpu": "L4", "torch": "2", "ultralytics": "8"})
    with pytest.raises(t.AmbienteDivergente):
        t.main(arquivo_g2=str(arq), destino_runs_drive=str(tmp_path))

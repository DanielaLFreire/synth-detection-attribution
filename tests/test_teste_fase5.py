"""Fase 5, §9: análise do teste, critério de réplica e verificações
pré-teste -- em dados fictícios, sem modelos."""
from __future__ import annotations

import hashlib
import json

import numpy as np
import pytest

from src.factorial.analise_fase5 import (
    BRACOS, ORCAMENTOS, SEEDS, F2C_NAO_APLICAVEL, analisar, analisar_teste, comparar_replicacao, tabela_markdown,
)


def _tabela(ef_s2=0.0, ef_s1=0.0, ruido=0.002, seed=3):
    rng = np.random.default_rng(seed)
    ef = {"S1": {"C": 0, "M25": ef_s1 / 2, "M50": ef_s1}, "S2": {"C": 0, "M25": ef_s2 / 2, "M50": ef_s2}}
    return {o: {b: {s: 0.69 + ef[o][b] + rng.normal(0, ruido) for s in SEEDS} for b in BRACOS} for o in ORCAMENTOS}


def test_analisar_teste_familias_e_f2c_declarada():
    t = _tabela()
    r = analisar_teste(t, t, t)
    assert [c["nome"].split(":")[0] for c in r["F1"]] == ["P11", "P12", "P13"]
    assert [c["nome"].split(":")[0] for c in r["F2"]] == ["F2a", "F2b", "F2d"]
    assert r["F2c"] == F2C_NAO_APLICAVEL and "save_period" in r["F2c"]
    assert all(c["p_holm"] is not None for c in r["F2"])
    json.dumps(r)
    assert "F3" not in tabela_markdown(r, familias=("F1", "F2"))


def test_replicacao_mesma_categoria():
    val = analisar(**{k: _tabela(ef_s2=-0.03, seed=1) for k in ("recall", "map50", "auc", "small")})
    teste_igual = analisar_teste(*[_tabela(ef_s2=-0.03, seed=2)] * 3)
    teste_nulo = analisar_teste(*[_tabela(ef_s2=0.0, ruido=0.001, seed=2)] * 3)
    r1 = {r["contraste"]: r for r in comparar_replicacao(val, teste_igual)}
    r2 = {r["contraste"]: r for r in comparar_replicacao(val, teste_nulo)}
    assert set(r1) == {"P11", "P12", "P13", "F2a", "F2b", "F2d"}  # F2c fica de fora
    assert r1["P11"]["replica"] and r1["P11"]["veredito_teste"] == "sintetico_pior"
    assert not r2["P11"]["replica"] and r2["P11"]["veredito_teste"] == "equivalente"


# --- verificar() com um "Drive" e um CITRA fictícios ---

def _ambiente(tmp_path, *, analise_val=True, marcador=False, adulterar=False, vazar=False):
    from src.train.passos_fixos import planejar_execucoes
    fase5, citra = tmp_path / "fase5", tmp_path / "citra"
    manifesto = {}
    for e in planejar_execucoes():
        w = fase5 / "runs" / e.nome / "weights"
        w.mkdir(parents=True)
        (w / "last.pt").write_bytes(e.nome.encode())
        manifesto[e.nome] = hashlib.sha256(e.nome.encode()).hexdigest()
    (fase5 / "modelos_fase5.json").write_text(json.dumps(manifesto), encoding="utf-8")
    if analise_val:
        (fase5 / "analise_val_executada.json").write_text("{}", encoding="utf-8")
    if marcador:
        (fase5 / "teste_avaliado.json").write_text(json.dumps({"avaliado_em_utc": "x"}), encoding="utf-8")
    if adulterar:
        (fase5 / "runs" / "f5_S2_M50_seed7" / "weights" / "last.pt").write_bytes(b"outro")
    for split, n in (("train", 4), ("val", 3), ("test", 3)):
        (citra / split / "images").mkdir(parents=True)
        (citra / split / "labels_final").mkdir(parents=True)
        for i in range(n):
            (citra / split / "images" / f"{split}{i}.jpg").write_bytes(f"{split}-{i}".encode())
            (citra / split / "labels_final" / f"{split}{i}.txt").write_text("0 0.5 0.5 0.1 0.1\n")
    man = tmp_path / "amostra.csv"
    base = "test0" if vazar else "train0"
    man.write_text(f"ordem,celula,arquivo,imagem_base,variacao,em_m25,sha256\n0,c,{base}_v0.png,{base},0,1,x\n", encoding="utf-8")
    return str(fase5), str(citra), man


def test_verificar_go(tmp_path):
    from scripts.avaliar_teste_fase5 import verificar
    f5, citra, man = _ambiente(tmp_path)
    assert verificar(f5, citra, man) == []


@pytest.mark.parametrize("kw,trecho", [
    ({"analise_val": False}, "análise de validação"),
    ({"marcador": True}, "marcador"),
    ({"adulterar": True}, "SHA-256"),
    ({"vazar": True}, "amostra sintética"),
])
def test_verificar_no_go(tmp_path, kw, trecho):
    from scripts.avaliar_teste_fase5 import verificar
    f5, citra, man = _ambiente(tmp_path, **kw)
    probs = verificar(f5, citra, man)
    assert any(trecho in p for p in probs)


def test_main_recusa_se_marcador_existe(tmp_path):
    pytest.importorskip("ultralytics")
    from src.evaluation.guarda_teste import AvaliacaoDeTesteJaRealizada
    from scripts.avaliar_teste_fase5 import main
    f5, citra, _ = _ambiente(tmp_path, marcador=True)
    with pytest.raises(AvaliacaoDeTesteJaRealizada):
        main(f5, citra)

from __future__ import annotations
from pathlib import Path
from src.evaluation import hashes_imagens, pareamento_imagens_labels, stems_em_manifesto, verificar_disjuncao


def test_duplicata_por_conteudo_detectada_mesmo_com_nome_diferente(tmp_path):
    a = tmp_path / "a"; b = tmp_path / "b"; a.mkdir(); b.mkdir()
    (a / "x.png").write_bytes(b"IMAGEM-1"); (b / "y.png").write_bytes(b"IMAGEM-1"); (b / "z.png").write_bytes(b"IMAGEM-2")
    ha, hb = hashes_imagens(a), hashes_imagens(b)
    comuns = set(ha) & set(hb)
    assert len(comuns) == 1 and hb[next(iter(comuns))] == "y"


def test_pareamento_aponta_faltantes(tmp_path):
    i = tmp_path / "i"; l = tmp_path / "l"; i.mkdir(); l.mkdir()
    (i / "1.jpg").write_bytes(b"x"); (i / "2.jpg").write_bytes(b"x"); (l / "1.txt").write_text(""); (l / "3.txt").write_text("")
    r = pareamento_imagens_labels(i, l)
    assert r["imagens_sem_label"] == ["2"] and r["labels_sem_imagem"] == ["3"]


def test_disjuncao_e_manifesto(tmp_path):
    m = tmp_path / "m.csv"; m.write_text("imagem_id,box_index\nA,0\nB,1\n")
    assert stems_em_manifesto(m) == {"A", "B"}
    assert stems_em_manifesto(tmp_path / "nao_existe.csv") == set()
    r = verificar_disjuncao({"A", "T"}, {"treino": {"A", "C"}, "val": {"D"}})
    assert r == {"treino": ["A"], "val": []}

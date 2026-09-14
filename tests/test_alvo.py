"""Testes da Fase 2 (Estágio A): construção do alvo binário por casamento
IoU entre caixas coladas e detecções, com agregação entre seeds."""
from __future__ import annotations

import csv
from pathlib import Path

from src.attribution import construir_alvo


def _escrever_manifesto(caminho: Path, caixas: list[dict]):
    """caixas: lista de dicts com cena_stem, x0, y0, x1, y1 (pixels)."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    campos = ["imagem_id", "box_index", "grupo_geometrico_id", "variacao_k",
              "caixa_x0_px", "caixa_y0_px", "caixa_x1_px", "caixa_y1_px",
              "fonte", "fator_reescala", "imagem_destino_path"]
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        for i, c in enumerate(caixas):
            w.writerow({
                "imagem_id": c["cena_stem"].split("_v")[0], "box_index": i,
                "grupo_geometrico_id": f"g{i}", "variacao_k": 0,
                "caixa_x0_px": c["x0"], "caixa_y0_px": c["y0"],
                "caixa_x1_px": c["x1"], "caixa_y1_px": c["y1"],
                "fonte": "FonteX", "fator_reescala": 1.0,
                "imagem_destino_path": f"/qualquer/pasta/{c['cena_stem']}.png",
            })


def _escrever_deteccoes(caminho: Path, deteccoes: list[dict]):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["seed_checkpoint", "cena_stem", "x0_px", "y0_px", "x1_px", "y1_px", "conf", "classe"])
        w.writeheader()
        for d in deteccoes:
            w.writerow({"seed_checkpoint": 42, "cena_stem": d["cena_stem"],
                        "x0_px": d["x0"], "y0_px": d["y0"], "x1_px": d["x1"], "y1_px": d["y1"],
                        "conf": d["conf"], "classe": 0})


def _ler_saida(caminho: Path) -> list[dict]:
    with open(caminho, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_deteccao_com_iou_alto_e_conf_alta_e_acerto(tmp_path):
    manifesto = tmp_path / "manifesto.csv"
    _escrever_manifesto(manifesto, [{"cena_stem": "img1_v00", "x0": 100, "y0": 100, "x1": 200, "y1": 200}])

    det = tmp_path / "det_42.csv"
    # detecção quase idêntica à caixa colada, confiança alta
    _escrever_deteccoes(det, [{"cena_stem": "img1_v00", "x0": 102, "y0": 101, "x1": 199, "y1": 202, "conf": 0.9}])

    resumo = construir_alvo(manifesto, {42: det}, tmp_path / "alvo.csv", iou_min=0.5, conf_min=0.25)
    linhas = _ler_saida(tmp_path / "alvo.csv")

    assert resumo["n_caixas"] == 1
    assert linhas[0]["acerto_seed42"] == "1"
    assert float(linhas[0]["conf_max_seed42"]) == 0.9
    assert linhas[0]["acerto_votacao"] == "1"


def test_deteccao_longe_da_caixa_colada_e_erro(tmp_path):
    manifesto = tmp_path / "manifesto.csv"
    _escrever_manifesto(manifesto, [{"cena_stem": "img1_v00", "x0": 100, "y0": 100, "x1": 200, "y1": 200}])

    det = tmp_path / "det_42.csv"
    # detecção em outro canto da imagem, sem sobreposição
    _escrever_deteccoes(det, [{"cena_stem": "img1_v00", "x0": 500, "y0": 500, "x1": 600, "y1": 600, "conf": 0.95}])

    resumo = construir_alvo(manifesto, {42: det}, tmp_path / "alvo.csv")
    linhas = _ler_saida(tmp_path / "alvo.csv")

    assert linhas[0]["acerto_seed42"] == "0"
    assert float(linhas[0]["conf_max_seed42"]) == 0.0  # nenhuma casou
    assert resumo["taxa_acerto_votacao"] == 0.0


def test_deteccao_com_iou_alto_mas_conf_baixa_e_erro_no_limiar(tmp_path):
    """Sobrepõe bem (IoU alto), mas a confiança fica abaixo do limiar --
    conf_max registra o valor real (score contínuo), mas acerto=0."""
    manifesto = tmp_path / "manifesto.csv"
    _escrever_manifesto(manifesto, [{"cena_stem": "img1_v00", "x0": 100, "y0": 100, "x1": 200, "y1": 200}])

    det = tmp_path / "det_42.csv"
    _escrever_deteccoes(det, [{"cena_stem": "img1_v00", "x0": 100, "y0": 100, "x1": 200, "y1": 200, "conf": 0.10}])

    construir_alvo(manifesto, {42: det}, tmp_path / "alvo.csv", conf_min=0.25)
    linhas = _ler_saida(tmp_path / "alvo.csv")

    assert float(linhas[0]["conf_max_seed42"]) == 0.10  # score contínuo preservado
    assert linhas[0]["acerto_seed42"] == "0"           # mas abaixo do limiar


def test_votacao_majoritaria_entre_tres_seeds(tmp_path):
    manifesto = tmp_path / "manifesto.csv"
    _escrever_manifesto(manifesto, [{"cena_stem": "img1_v00", "x0": 100, "y0": 100, "x1": 200, "y1": 200}])

    # seed 42 e 123 acertam, seed 2024 erra -> maioria (2 de 3) = acerto
    det42 = tmp_path / "det_42.csv"
    det123 = tmp_path / "det_123.csv"
    det2024 = tmp_path / "det_2024.csv"
    _escrever_deteccoes(det42, [{"cena_stem": "img1_v00", "x0": 100, "y0": 100, "x1": 200, "y1": 200, "conf": 0.8}])
    _escrever_deteccoes(det123, [{"cena_stem": "img1_v00", "x0": 100, "y0": 100, "x1": 200, "y1": 200, "conf": 0.7}])
    _escrever_deteccoes(det2024, [])  # nenhuma detecção nessa cena

    resumo = construir_alvo(manifesto, {42: det42, 123: det123, 2024: det2024}, tmp_path / "alvo.csv")
    linhas = _ler_saida(tmp_path / "alvo.csv")

    assert linhas[0]["acerto_seed42"] == "1"
    assert linhas[0]["acerto_seed123"] == "1"
    assert linhas[0]["acerto_seed2024"] == "0"
    assert linhas[0]["acerto_votacao"] == "1"
    assert abs(float(linhas[0]["conf_media"]) - (0.8 + 0.7 + 0.0) / 3) < 1e-4
    assert resumo["taxa_acerto_votacao"] == 1.0


def test_votacao_com_apenas_uma_seed_acertando_e_erro(tmp_path):
    manifesto = tmp_path / "manifesto.csv"
    _escrever_manifesto(manifesto, [{"cena_stem": "img1_v00", "x0": 100, "y0": 100, "x1": 200, "y1": 200}])

    det42 = tmp_path / "det_42.csv"
    det123 = tmp_path / "det_123.csv"
    det2024 = tmp_path / "det_2024.csv"
    _escrever_deteccoes(det42, [{"cena_stem": "img1_v00", "x0": 100, "y0": 100, "x1": 200, "y1": 200, "conf": 0.9}])
    _escrever_deteccoes(det123, [])
    _escrever_deteccoes(det2024, [])

    construir_alvo(manifesto, {42: det42, 123: det123, 2024: det2024}, tmp_path / "alvo.csv")
    linhas = _ler_saida(tmp_path / "alvo.csv")
    assert linhas[0]["acerto_votacao"] == "0"  # 1 de 3 não é maioria


def test_deteccoes_de_outra_cena_nao_contaminam(tmp_path):
    """Uma detecção perfeitamente sobreposta, mas em OUTRA cena, não deve
    contar -- o casamento é sempre dentro da mesma cena."""
    manifesto = tmp_path / "manifesto.csv"
    _escrever_manifesto(manifesto, [{"cena_stem": "img1_v00", "x0": 100, "y0": 100, "x1": 200, "y1": 200}])

    det = tmp_path / "det_42.csv"
    _escrever_deteccoes(det, [{"cena_stem": "img1_v01", "x0": 100, "y0": 100, "x1": 200, "y1": 200, "conf": 0.99}])

    construir_alvo(manifesto, {42: det}, tmp_path / "alvo.csv")
    linhas = _ler_saida(tmp_path / "alvo.csv")
    assert linhas[0]["acerto_seed42"] == "0"


def test_todas_as_colunas_do_manifesto_sao_preservadas(tmp_path):
    """A tabela de alvo deve carregar todas as colunas do manifesto de
    composição -- são as features do Estágio A, não podem se perder."""
    manifesto = tmp_path / "manifesto.csv"
    _escrever_manifesto(manifesto, [{"cena_stem": "img1_v00", "x0": 100, "y0": 100, "x1": 200, "y1": 200}])
    det = tmp_path / "det_42.csv"
    _escrever_deteccoes(det, [])

    construir_alvo(manifesto, {42: det}, tmp_path / "alvo.csv")
    linhas = _ler_saida(tmp_path / "alvo.csv")

    for coluna in ("grupo_geometrico_id", "fonte", "fator_reescala", "caixa_x0_px"):
        assert coluna in linhas[0]

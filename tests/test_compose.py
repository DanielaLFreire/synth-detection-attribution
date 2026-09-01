"""
Testes de integridade do componente de composição (tarefa -1.2).

Usa dados sintéticos pequenos gerados em tempo de teste -- não depende do
Drive real. Cobre exatamente as três decisões de design que justificam a
existência deste módulo (ver docstring de src/compose/compose.py):

1. o manifesto tem exatamente uma linha por (caixa x variação) gerada;
2. rodar duas vezes com a mesma seed produz manifesto e imagens idênticos
   (determinismo -- mesmo princípio da tarefa 1.2 do cronograma, aplicado
   aqui em miniatura, antes de qualquer GPU envolvida);
3. compor sobre o split "train" é bloqueado por padrão (§5.2 do plano).
"""
from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import pytest
from PIL import Image

from src.compose import compor_dataset, SplitDeTreinoBloqueado


def _criar_dataset_alvo_sintetico(tmp_path: Path, n_imagens: int = 3, n_caixas_por_imagem: int = 2):
    """Cria um mini dataset-alvo (imagens + labels YOLO) para teste."""
    imagens_dir = tmp_path / "alvo" / "images"
    labels_dir = tmp_path / "alvo" / "labels"
    imagens_dir.mkdir(parents=True)
    labels_dir.mkdir(parents=True)

    largura, altura = 200, 100  # deliberadamente não-quadrado, como o CITRA real
    for i in range(n_imagens):
        img = Image.new("RGB", (largura, altura), color=(30, 60, 90))
        img.save(imagens_dir / f"img{i}.png")

        linhas = []
        for j in range(n_caixas_por_imagem):
            cx = 0.2 + 0.1 * j
            cy = 0.5
            w, h = 0.1, 0.1
            linhas.append(f"0 {cx} {cy} {w} {h}")
        (labels_dir / f"img{i}.txt").write_text("\n".join(linhas) + "\n")

    return imagens_dir, labels_dir


def _criar_pool_crops_sintetico(tmp_path: Path, n_crops: int = 5):
    """Cria um pool pequeno de crops de uma fonte fictícia."""
    crops_dir = tmp_path / "crops_fonte_fake"
    crops_dir.mkdir(parents=True)
    pool = []
    for i in range(n_crops):
        crop = Image.new("RGBA", (40 + i * 5, 20 + i * 3), color=(200, 10, 10, 255))
        caminho = crops_dir / f"crop_{i}.png"
        crop.save(caminho)
        pool.append(("FonteFake", caminho))
    return pool


def _hash_arquivo(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def test_manifesto_tem_uma_linha_por_caixa_vezes_variacao(tmp_path):
    n_imagens, n_caixas, n_variacoes = 3, 2, 4
    imagens_dir, labels_dir = _criar_dataset_alvo_sintetico(tmp_path, n_imagens, n_caixas)
    pool = _criar_pool_crops_sintetico(tmp_path)

    n_gerado = compor_dataset(
        imagens_alvo_dir=imagens_dir,
        labels_alvo_dir=labels_dir,
        pool_crops=pool,
        saida_imagens_dir=tmp_path / "saida" / "images",
        saida_labels_dir=tmp_path / "saida" / "labels",
        manifesto_csv=tmp_path / "manifesto.csv",
        manifesto_metadata_json=tmp_path / "manifesto_metadata.json",
        split="val",
        n_variacoes=n_variacoes,
        seed=42,
    )

    esperado = n_imagens * n_caixas * n_variacoes
    assert n_gerado == esperado, (
        f"esperado {esperado} colagens ({n_imagens} imagens x {n_caixas} caixas x "
        f"{n_variacoes} variações), obtido {n_gerado}"
    )

    with open(tmp_path / "manifesto.csv", newline="", encoding="utf-8") as f:
        linhas = list(csv.DictReader(f))
    assert len(linhas) == esperado, "número de linhas do CSV não bate com o retornado pela função"

    # cada grupo geométrico (imagem, caixa) deve aparecer exatamente n_variacoes vezes
    from collections import Counter
    contagem_por_grupo = Counter(l["grupo_geometrico_id"] for l in linhas)
    assert len(contagem_por_grupo) == n_imagens * n_caixas
    assert all(c == n_variacoes for c in contagem_por_grupo.values()), (
        "cada grupo (imagem, caixa) deve ter exatamente n_variacoes linhas -- "
        "ver §5.1 do plano sobre agrupamento geométrico"
    )


def test_determinismo_mesma_seed_produz_saida_identica(tmp_path):
    imagens_dir, labels_dir = _criar_dataset_alvo_sintetico(tmp_path, n_imagens=2, n_caixas_por_imagem=2)
    pool = _criar_pool_crops_sintetico(tmp_path)

    def rodar(pasta_saida: Path, caminho_manifesto: Path):
        compor_dataset(
            imagens_alvo_dir=imagens_dir,
            labels_alvo_dir=labels_dir,
            pool_crops=pool,
            saida_imagens_dir=pasta_saida / "images",
            saida_labels_dir=pasta_saida / "labels",
            manifesto_csv=caminho_manifesto,
            manifesto_metadata_json=pasta_saida / "meta.json",
            split="val",
            n_variacoes=2,
            seed=123,
        )

    rodar(tmp_path / "run1", tmp_path / "manifesto1.csv")
    rodar(tmp_path / "run2", tmp_path / "manifesto2.csv")

    imgs1 = sorted((tmp_path / "run1" / "images").glob("*.png"))
    imgs2 = sorted((tmp_path / "run2" / "images").glob("*.png"))
    assert len(imgs1) == len(imgs2) and len(imgs1) > 0

    for i1, i2 in zip(imgs1, imgs2):
        assert _hash_arquivo(i1) == _hash_arquivo(i2), (
            f"determinismo quebrado: {i1.name} difere entre as duas execuções "
            "com a mesma seed"
        )

    # colunas não-temporais do manifesto (excluindo run_id e timestamp, que
    # mudam por execução por design) também devem bater
    def ler_sem_colunas_variaveis(caminho):
        with open(caminho, newline="", encoding="utf-8") as f:
            linhas = list(csv.DictReader(f))
        for l in linhas:
            l.pop("run_id", None)
            l.pop("timestamp_geracao", None)
            l.pop("imagem_destino_path", None)
            l.pop("label_destino_path", None)
        return linhas

    assert ler_sem_colunas_variaveis(tmp_path / "manifesto1.csv") == \
        ler_sem_colunas_variaveis(tmp_path / "manifesto2.csv")


def test_split_treino_bloqueado_por_padrao(tmp_path):
    imagens_dir, labels_dir = _criar_dataset_alvo_sintetico(tmp_path)
    pool = _criar_pool_crops_sintetico(tmp_path)

    with pytest.raises(SplitDeTreinoBloqueado):
        compor_dataset(
            imagens_alvo_dir=imagens_dir,
            labels_alvo_dir=labels_dir,
            pool_crops=pool,
            saida_imagens_dir=tmp_path / "saida" / "images",
            saida_labels_dir=tmp_path / "saida" / "labels",
            manifesto_csv=tmp_path / "manifesto.csv",
            manifesto_metadata_json=tmp_path / "manifesto_metadata.json",
            split="train",
            n_variacoes=1,
            seed=42,
        )


def test_split_treino_permitido_com_override_explicito(tmp_path, capsys):
    imagens_dir, labels_dir = _criar_dataset_alvo_sintetico(tmp_path)
    pool = _criar_pool_crops_sintetico(tmp_path)

    n_gerado = compor_dataset(
        imagens_alvo_dir=imagens_dir,
        labels_alvo_dir=labels_dir,
        pool_crops=pool,
        saida_imagens_dir=tmp_path / "saida" / "images",
        saida_labels_dir=tmp_path / "saida" / "labels",
        manifesto_csv=tmp_path / "manifesto.csv",
        manifesto_metadata_json=tmp_path / "manifesto_metadata.json",
        split="train",
        n_variacoes=1,
        seed=42,
        permitir_split_treino=True,
    )
    assert n_gerado > 0
    saida_console = capsys.readouterr().out
    assert "AVISO" in saida_console, "o override deve imprimir um aviso explícito"

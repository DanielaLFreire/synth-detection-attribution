"""Testes da tarefa -1.4: materialização de labels_final com validação de
integridade e detecção de deriva via hash."""
from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from src.materialize import (
    materializar_labels_final,
    verificar_labels_final,
    InconsistenciaDeDataset,
)


def _criar_split_sintetico(root: Path, split: str, imagens_e_labels: dict[str, str]):
    """imagens_e_labels: {stem: conteudo_do_label_ou_None}. Se None, a
    imagem é criada mas o label NÃO -- para testar detecção de órfão."""
    imagens_dir = root / split / "images"
    labels_dir = root / split / "labels_single_class"
    imagens_dir.mkdir(parents=True, exist_ok=True)
    labels_dir.mkdir(parents=True, exist_ok=True)

    for stem, conteudo in imagens_e_labels.items():
        Image.new("RGB", (100, 60), color=(1, 2, 3)).save(imagens_dir / f"{stem}.png")
        if conteudo is not None:
            (labels_dir / f"{stem}.txt").write_text(conteudo)


def test_materializacao_caso_limpo(tmp_path):
    _criar_split_sintetico(tmp_path, "val", {
        "img1": "0 0.5 0.5 0.1 0.1\n0 0.3 0.3 0.05 0.05\n",
        "img2": "0 0.2 0.2 0.1 0.1\n",
    })

    relatorios = materializar_labels_final(
        root_dataset_alvo=tmp_path,
        labels_subfolder_origem="labels_single_class",
        splits=["val"],
    )

    assert len(relatorios) == 1
    r = relatorios[0]
    assert r.split == "val"
    assert r.n_imagens == 2
    assert r.n_labels_copiados == 2
    assert r.n_boxes_total == 3  # 2 caixas em img1 + 1 em img2

    labels_final_dir = tmp_path / "val" / "labels_final"
    assert (labels_final_dir / "img1.txt").exists()
    assert (labels_final_dir / "img2.txt").exists()
    assert (tmp_path / "val" / "labels_final_manifest.json").exists()


def test_materializacao_detecta_imagem_sem_label(tmp_path):
    _criar_split_sintetico(tmp_path, "val", {
        "img1": "0 0.5 0.5 0.1 0.1\n",
        "img_orfa": None,  # imagem existe, label não -- deve ser detectado
    })

    with pytest.raises(InconsistenciaDeDataset, match="sem label"):
        materializar_labels_final(
            root_dataset_alvo=tmp_path,
            labels_subfolder_origem="labels_single_class",
            splits=["val"],
        )


def test_materializacao_detecta_classe_invalida(tmp_path):
    """Reproduz em miniatura exatamente o tipo de contaminação real
    encontrada no CITRA-3D-Real (linha 'Quadrado_marcacao(Clone)') --
    confirma que o script teria detectado isso sozinho, sem depender de
    uma quarentena manual feita à parte."""
    _criar_split_sintetico(tmp_path, "train", {
        "img_boa": "0 0.5 0.5 0.1 0.1\n",
        "img_contaminada": "0 0.4 0.4 0.1 0.1\nQuadrado_marcacao(Clone) 0.53 0.90 0 0\n",
    })

    with pytest.raises(InconsistenciaDeDataset, match="Quadrado_marcacao"):
        materializar_labels_final(
            root_dataset_alvo=tmp_path,
            labels_subfolder_origem="labels_single_class",
            splits=["train"],
        )


def test_materializacao_detecta_classe_multipla_nao_permitida(tmp_path):
    """Se alguém apontar por engano para uma pasta de labels multi-classe
    (ex.: 'labels/' em vez de 'labels_single_class/'), a materialização
    deve recusar, não silenciosamente aceitar classes 1-8."""
    _criar_split_sintetico(tmp_path, "test", {
        "img1": "3 0.5 0.5 0.1 0.1\n",  # classe 3, não permitida (só "0")
    })

    with pytest.raises(InconsistenciaDeDataset, match="classe '3'"):
        materializar_labels_final(
            root_dataset_alvo=tmp_path,
            labels_subfolder_origem="labels_single_class",
            splits=["test"],
        )


def test_verificacao_ok_quando_nada_mudou(tmp_path):
    _criar_split_sintetico(tmp_path, "val", {"img1": "0 0.5 0.5 0.1 0.1\n"})
    materializar_labels_final(
        root_dataset_alvo=tmp_path, labels_subfolder_origem="labels_single_class", splits=["val"],
    )

    relatorio = verificar_labels_final(tmp_path, "val")
    assert relatorio.ok is True
    assert relatorio.arquivos_alterados == []
    assert relatorio.arquivos_faltando == []


def test_verificacao_detecta_arquivo_alterado_depois_da_materializacao(tmp_path):
    """Este é o teste que justifica a existência da função de verificação:
    simula uma deriva (alguém edita o labels_final/ depois de materializado)
    e confirma que ela é detectada via hash, não por acaso."""
    _criar_split_sintetico(tmp_path, "val", {"img1": "0 0.5 0.5 0.1 0.1\n"})
    materializar_labels_final(
        root_dataset_alvo=tmp_path, labels_subfolder_origem="labels_single_class", splits=["val"],
    )

    # simula alguém editando o labels_final DEPOIS de congelado
    caminho = tmp_path / "val" / "labels_final" / "img1.txt"
    caminho.write_text("0 0.9 0.9 0.2 0.2\n")

    relatorio = verificar_labels_final(tmp_path, "val")
    assert relatorio.ok is False
    assert "img1" in relatorio.arquivos_alterados


def test_verificacao_detecta_arquivo_faltando(tmp_path):
    _criar_split_sintetico(tmp_path, "val", {
        "img1": "0 0.5 0.5 0.1 0.1\n",
        "img2": "0 0.2 0.2 0.1 0.1\n",
    })
    materializar_labels_final(
        root_dataset_alvo=tmp_path, labels_subfolder_origem="labels_single_class", splits=["val"],
    )

    (tmp_path / "val" / "labels_final" / "img2.txt").unlink()

    relatorio = verificar_labels_final(tmp_path, "val")
    assert relatorio.ok is False
    assert "img2" in relatorio.arquivos_faltando

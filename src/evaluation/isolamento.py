"""
Verificações de isolamento do split de teste ANTES da avaliação única
(Fase 4). Nenhuma predição, nenhum modelo -- só estrutura e conjuntos.
"""
from __future__ import annotations

import csv
import hashlib
from pathlib import Path

EXT_IMG = (".jpg", ".jpeg", ".png")


def hash_arquivo(caminho: Path) -> str:
    h = hashlib.md5()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def stems_imagens(pasta: Path) -> set[str]:
    return {p.stem for p in Path(pasta).iterdir() if p.suffix.lower() in EXT_IMG}


def hashes_imagens(pasta: Path) -> dict[str, str]:
    """{hash: stem} -- para detectar duplicatas por conteúdo entre splits."""
    return {hash_arquivo(p): p.stem for p in sorted(Path(pasta).iterdir()) if p.suffix.lower() in EXT_IMG}


def pareamento_imagens_labels(pasta_imgs: Path, pasta_lbls: Path) -> dict:
    imgs = stems_imagens(pasta_imgs)
    lbls = {p.stem for p in Path(pasta_lbls).glob("*.txt")}
    return {"n_imagens": len(imgs), "n_labels": len(lbls),
            "imagens_sem_label": sorted(imgs - lbls), "labels_sem_imagem": sorted(lbls - imgs)}


def stems_em_manifesto(caminho_csv: Path, coluna: str = "imagem_id") -> set[str]:
    if not Path(caminho_csv).exists():
        return set()
    with open(caminho_csv, newline="", encoding="utf-8") as f:
        return {l[coluna] for l in csv.DictReader(f) if coluna in l}


def verificar_disjuncao(teste: set[str], outros: dict[str, set[str]]) -> dict[str, list[str]]:
    """{nome_do_conjunto: [stems do teste que aparecem nele]} -- tudo deve ser vazio."""
    return {nome: sorted(teste & s) for nome, s in outros.items()}

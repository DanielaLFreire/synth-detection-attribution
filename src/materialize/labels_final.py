"""
Materialização de `labels_final/` (tarefa -1.4, §8.4 do plano).

Problema que este módulo resolve: o dataset-alvo tinha, no projeto anterior,
três pastas de labels candidatas (`labels/`, `labels_cleaned/`,
`labels_single_class/`), sem nenhuma delas ser explicitamente "a versão
final" -- a conversão para classe única acontecia em runtime, a cada sessão,
sem artefato congelado (ver docs/CHANGELOG_metodologico.md). Este projeto
materializa `labels_final/` uma vez, com um manifesto de hash SHA-256 por
arquivo, para que qualquer deriva futura no dado seja detectável.

Duas operações, deliberadamente separadas:
- `materializar_labels_final(...)`: valida e copia, gera o manifesto.
- `verificar_labels_final(...)`: recalcula hashes do estado atual e compara
  contra o manifesto congelado -- para rodar a qualquer momento no futuro,
  sem precisar confiar em memória de que "nada mudou".
"""
from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

MANIFEST_LABELS_FINAL_VERSION = "1.0"
_EXTENSOES_IMAGEM = (".png", ".jpg", ".jpeg")


class InconsistenciaDeDataset(RuntimeError):
    """Levantado quando a materialização encontra algo que não deveria
    existir num dataset-alvo pronto para uso: imagem sem label, label sem
    imagem, ou linha de label fora do padrão de classe única esperado."""


@dataclass
class RelatorioMaterializacao:
    split: str
    n_imagens: int
    n_labels_copiados: int
    n_boxes_total: int
    caminho_manifesto: Path


@dataclass
class RelatorioVerificacao:
    ok: bool
    arquivos_alterados: list[str] = field(default_factory=list)
    arquivos_faltando: list[str] = field(default_factory=list)
    arquivos_novos_nao_registrados: list[str] = field(default_factory=list)


def _sha256_arquivo(caminho: Path) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(65536), b""):
            h.update(bloco)
    return h.hexdigest()


def _validar_split_e_listar(
    imagens_dir: Path, labels_origem_dir: Path, classes_permitidas: set[str],
) -> list[str]:
    """Valida correspondência 1:1 imagem<->label e conteúdo de classe.
    Levanta InconsistenciaDeDataset se algo não bater -- não tenta
    "consertar sozinho" nem ignora silenciosamente."""
    imagens = {p.stem for p in imagens_dir.iterdir() if p.suffix.lower() in _EXTENSOES_IMAGEM}
    labels = {p.stem for p in labels_origem_dir.glob("*.txt")}

    imagens_sem_label = sorted(imagens - labels)
    labels_sem_imagem = sorted(labels - imagens)
    if imagens_sem_label:
        raise InconsistenciaDeDataset(
            f"{len(imagens_sem_label)} imagem(ns) sem label correspondente em "
            f"{labels_origem_dir}: {imagens_sem_label[:5]}{'...' if len(imagens_sem_label) > 5 else ''}"
        )
    if labels_sem_imagem:
        raise InconsistenciaDeDataset(
            f"{len(labels_sem_imagem)} label(s) sem imagem correspondente em "
            f"{imagens_dir}: {labels_sem_imagem[:5]}{'...' if len(labels_sem_imagem) > 5 else ''}"
        )

    for stem in sorted(labels):
        caminho = labels_origem_dir / f"{stem}.txt"
        with open(caminho, "r", encoding="utf-8") as f:
            for n_linha, linha in enumerate(f, start=1):
                partes = linha.split()
                if not partes:
                    continue
                classe = partes[0]
                if classe not in classes_permitidas:
                    raise InconsistenciaDeDataset(
                        f"{caminho}:{n_linha} tem classe '{classe}', fora do "
                        f"conjunto permitido {classes_permitidas} -- "
                        "materialização abortada, dado não está pronto."
                    )

    return sorted(labels)


def materializar_labels_final(
    *,
    root_dataset_alvo: Path,
    labels_subfolder_origem: str,
    splits: list[str],
    classes_permitidas: set[str] = frozenset({"0"}),
) -> list[RelatorioMaterializacao]:
    """Copia labels_subfolder_origem/ para labels_final/ em cada split,
    validando integridade antes, e grava um manifesto com hash por arquivo.

    O manifesto é gravado em `root_dataset_alvo/{split}/labels_final_manifest.json`.
    """
    root_dataset_alvo = Path(root_dataset_alvo)
    relatorios = []

    for split in splits:
        imagens_dir = root_dataset_alvo / split / "images"
        labels_origem_dir = root_dataset_alvo / split / labels_subfolder_origem
        labels_final_dir = root_dataset_alvo / split / "labels_final"

        if not imagens_dir.is_dir():
            raise InconsistenciaDeDataset(f"pasta de imagens não encontrada: {imagens_dir}")
        if not labels_origem_dir.is_dir():
            raise InconsistenciaDeDataset(f"pasta de labels de origem não encontrada: {labels_origem_dir}")

        stems_validados = _validar_split_e_listar(imagens_dir, labels_origem_dir, classes_permitidas)

        labels_final_dir.mkdir(parents=True, exist_ok=True)
        entradas_manifesto = []
        n_boxes_total = 0

        for stem in stems_validados:
            origem = labels_origem_dir / f"{stem}.txt"
            destino = labels_final_dir / f"{stem}.txt"
            shutil.copyfile(origem, destino)

            with open(destino, "r", encoding="utf-8") as f:
                linhas = [l for l in f.readlines() if l.strip()]
            n_boxes_total += len(linhas)

            entradas_manifesto.append({
                "imagem_id": stem,
                "sha256": _sha256_arquivo(destino),
                "n_boxes": len(linhas),
            })

        caminho_manifesto = root_dataset_alvo / split / "labels_final_manifest.json"
        manifesto = {
            "manifest_version": MANIFEST_LABELS_FINAL_VERSION,
            "split": split,
            "fonte_origem": labels_subfolder_origem,
            "classes_permitidas": sorted(classes_permitidas),
            "gerado_em_utc": datetime.now(timezone.utc).isoformat(),
            "n_arquivos": len(entradas_manifesto),
            "n_boxes_total": n_boxes_total,
            "arquivos": entradas_manifesto,
        }
        caminho_manifesto.write_text(json.dumps(manifesto, indent=2, ensure_ascii=False), encoding="utf-8")

        relatorios.append(RelatorioMaterializacao(
            split=split,
            n_imagens=len(stems_validados),
            n_labels_copiados=len(entradas_manifesto),
            n_boxes_total=n_boxes_total,
            caminho_manifesto=caminho_manifesto,
        ))

    return relatorios


def verificar_labels_final(root_dataset_alvo: Path, split: str) -> RelatorioVerificacao:
    """Recalcula os hashes de labels_final/{split} e compara contra o
    manifesto congelado -- roda a qualquer momento para detectar deriva."""
    root_dataset_alvo = Path(root_dataset_alvo)
    labels_final_dir = root_dataset_alvo / split / "labels_final"
    caminho_manifesto = root_dataset_alvo / split / "labels_final_manifest.json"

    if not caminho_manifesto.exists():
        raise FileNotFoundError(
            f"manifesto não encontrado em {caminho_manifesto} -- rode "
            "materializar_labels_final() primeiro."
        )
    manifesto = json.loads(caminho_manifesto.read_text(encoding="utf-8"))
    hashes_esperados = {e["imagem_id"]: e["sha256"] for e in manifesto["arquivos"]}

    hashes_atuais = {}
    for caminho in labels_final_dir.glob("*.txt"):
        hashes_atuais[caminho.stem] = _sha256_arquivo(caminho)

    alterados = sorted(
        stem for stem in hashes_esperados
        if stem in hashes_atuais and hashes_atuais[stem] != hashes_esperados[stem]
    )
    faltando = sorted(stem for stem in hashes_esperados if stem not in hashes_atuais)
    novos_nao_registrados = sorted(stem for stem in hashes_atuais if stem not in hashes_esperados)

    ok = not (alterados or faltando or novos_nao_registrados)
    return RelatorioVerificacao(
        ok=ok,
        arquivos_alterados=alterados,
        arquivos_faltando=faltando,
        arquivos_novos_nao_registrados=novos_nao_registrados,
    )

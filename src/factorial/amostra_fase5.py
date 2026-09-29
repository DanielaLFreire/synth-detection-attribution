"""
Fase 5 -- amostra do conjunto sintético (adendo 3 §4.3).

- Origem: imagens sintéticas das 4 células da Fase 3, DEPOIS da remoção
  das cópias sem colagem (commit d82223d): 2.592 por célula.
- M50: 674 por célula, sem reposição, semente 20260928 -> 2.696 imagens.
- M25: as primeiras 337 de cada célula NA ORDEM DA AMOSTRAGEM (aninhado
  em M50) -> 1.348 imagens.

Determinismo: o gerador de cada célula é `random.Random(f"{semente}:{celula}")`.
Semente em string é determinística em qualquer execução do CPython 3
(não depende de PYTHONHASHSEED). A lista de candidatas é ordenada por nome
antes do sorteio, para não depender da ordem do sistema de arquivos.

O manifesto grava apenas caminhos RELATIVOS (célula + nome do arquivo) e
o SHA-256 de cada imagem: o hash do manifesto não depende de onde as
células foram extraídas (Colab, máquina local) e prova o conteúdo exato.
"""
from __future__ import annotations

import csv
import hashlib
import random
from dataclasses import dataclass
from pathlib import Path

CELULAS_FASE3 = ("casada__alto", "casada__baixo", "reduzida__alto", "reduzida__baixo")
SEMENTE_AMOSTRA = 20260928
N_POR_CELULA_ESPERADO = 2592
N_POR_CELULA_M50 = 674
N_POR_CELULA_M25 = 337

COLUNAS_MANIFESTO = ("ordem", "celula", "arquivo", "imagem_base", "variacao", "em_m25", "sha256")


class AmostraInvalida(ValueError):
    pass


def _sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(65536), b""):
            h.update(bloco)
    return h.hexdigest()


def decompor_nome(nome_arquivo: str) -> tuple[str, int]:
    """`{imagem_id}_v{k}.png` -> (imagem_id, k); convenção de
    src/factorial/celulas.py (remover_sinteticas_sem_colagem)."""
    stem = Path(nome_arquivo).stem
    if "_v" not in stem:
        raise AmostraInvalida(f"Nome fora da convenção '{{imagem_id}}_v{{k}}': {nome_arquivo}")
    base, k = stem.rsplit("_v", 1)
    if not k.isdigit():
        raise AmostraInvalida(f"Variação não numérica em: {nome_arquivo}")
    return base, int(k)


def listar_sinteticas(pasta_imagens: Path) -> list[Path]:
    return sorted(Path(pasta_imagens).glob("*_v*.png"), key=lambda p: p.name)


def amostrar_por_celula(
    pastas_imagens: dict[str, Path],
    n_por_celula: int = N_POR_CELULA_M50,
    semente: int = SEMENTE_AMOSTRA,
    n_esperado_por_celula: int | None = N_POR_CELULA_ESPERADO,
) -> dict[str, list[Path]]:
    """Amostra sem reposição, estratificada por célula. A ordem de cada
    lista devolvida É a ordem do sorteio (usada para o aninhamento de M25)."""
    faltando = set(CELULAS_FASE3) - set(pastas_imagens)
    if faltando:
        raise AmostraInvalida(f"Células ausentes: {sorted(faltando)}")
    amostra: dict[str, list[Path]] = {}
    for celula in CELULAS_FASE3:
        candidatas = listar_sinteticas(pastas_imagens[celula])
        if n_esperado_por_celula is not None and len(candidatas) != n_esperado_por_celula:
            raise AmostraInvalida(
                f"{celula}: {len(candidatas)} sintéticas, esperado {n_esperado_por_celula} "
                "(as cópias sem colagem foram removidas?)"
            )
        if len(candidatas) < n_por_celula:
            raise AmostraInvalida(f"{celula}: {len(candidatas)} candidatas < {n_por_celula} pedidas.")
        rng = random.Random(f"{semente}:{celula}")
        amostra[celula] = rng.sample(candidatas, n_por_celula)
    return amostra


def subconjunto_aninhado(amostra: dict[str, list[Path]], n_por_celula: int = N_POR_CELULA_M25) -> dict[str, list[Path]]:
    for celula, lista in amostra.items():
        if len(lista) < n_por_celula:
            raise AmostraInvalida(f"{celula}: amostra com {len(lista)} < {n_por_celula}.")
    return {celula: lista[:n_por_celula] for celula, lista in amostra.items()}


def achatar(amostra: dict[str, list[Path]]) -> list[Path]:
    return [p for celula in CELULAS_FASE3 for p in amostra[celula]]


def escrever_manifesto(
    amostra: dict[str, list[Path]],
    destino_csv: Path,
    n_por_celula_m25: int = N_POR_CELULA_M25,
) -> int:
    """Grava o manifesto (só caminhos relativos) e devolve o nº de linhas."""
    destino_csv = Path(destino_csv)
    destino_csv.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with open(destino_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(COLUNAS_MANIFESTO)
        for celula in CELULAS_FASE3:
            for ordem, caminho in enumerate(amostra[celula]):
                base, k = decompor_nome(caminho.name)
                w.writerow([
                    ordem, celula, caminho.name, base, k,
                    int(ordem < n_por_celula_m25), _sha256(caminho),
                ])
                n += 1
    return n


@dataclass(frozen=True)
class LinhaManifesto:
    ordem: int
    celula: str
    arquivo: str
    em_m25: bool
    sha256: str


def ler_manifesto(caminho_csv: Path) -> list[LinhaManifesto]:
    with open(caminho_csv, newline="", encoding="utf-8") as f:
        leitor = csv.DictReader(f)
        if tuple(leitor.fieldnames or ()) != COLUNAS_MANIFESTO:
            raise AmostraInvalida(f"Colunas inesperadas: {leitor.fieldnames}")
        return [
            LinhaManifesto(int(r["ordem"]), r["celula"], r["arquivo"], r["em_m25"] == "1", r["sha256"])
            for r in leitor
        ]


def resolver_manifesto(
    caminho_csv: Path,
    pastas_imagens: dict[str, Path],
    somente_m25: bool = False,
    conferir_hash: bool = True,
) -> list[Path]:
    """Converte o manifesto em caminhos absolutos na máquina atual,
    conferindo que cada arquivo existe e (por padrão) que o SHA-256 bate.
    É assim que a preparação dos dados usa a amostra: nunca re-sorteia."""
    caminhos = []
    for linha in ler_manifesto(caminho_csv):
        if somente_m25 and not linha.em_m25:
            continue
        p = Path(pastas_imagens[linha.celula]) / linha.arquivo
        if not p.exists():
            raise AmostraInvalida(f"Arquivo do manifesto ausente: {p}")
        if conferir_hash and _sha256(p) != linha.sha256:
            raise AmostraInvalida(f"SHA-256 diverge do manifesto: {p}")
        caminhos.append(p)
    return caminhos

"""
Deduplicação de imagens aumentadas por exportação Roboflow.

Achado que motiva este módulo (ver docs/CHANGELOG_metodologico.md,
2026-08-31): o `SeaShips_voc.zip` disponível continha 13.105 imagens, das
quais apenas 6.979 são bases únicas -- o Roboflow aplicou aumento de dados
(flip/rotação/brilho) sobre a maior parte do conjunto de treino ao exportar,
preservando o nome-base e variando apenas o sufixo de hash.

Convenção de nome do Roboflow: "<nome_base>_jpg.rf.<hash_hex>.<ext>"
"""
from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

_PADRAO_ROBOFLOW = re.compile(r"^(.*)_jpg\.rf\.[a-f0-9]+\.(jpg|jpeg|png)$", re.IGNORECASE)


@dataclass
class ResultadoDeduplicacao:
    mantidos: list[Path]
    descartados: list[Path]
    sem_padrao_reconhecido: list[Path]

    @property
    def n_bases_unicas(self) -> int:
        return len(self.mantidos)


def identificar_base_roboflow(nome_arquivo: str) -> str | None:
    """Extrai o nome-base de um arquivo exportado pelo Roboflow. Retorna
    None se o nome não seguir o padrão reconhecido (ver docstring do
    módulo) -- isso é reportado explicitamente, nunca descartado em
    silêncio, porque um padrão não reconhecido pode indicar uma fonte
    diferente do que se espera."""
    m = _PADRAO_ROBOFLOW.match(nome_arquivo)
    return m.group(1) if m else None


def deduplicar_por_base(
    caminhos: list[Path],
    estrategia: str = "primeiro_alfabetico",
) -> ResultadoDeduplicacao:
    """Agrupa arquivos pelo nome-base do Roboflow e mantém exatamente um
    por base.

    `estrategia="primeiro_alfabetico"`: mantém, dentro de cada grupo, o
    arquivo cujo caminho completo vem primeiro em ordem alfabética -- é
    determinístico e documentável (não é necessariamente "o original" antes
    da augmentation, já que o Roboflow não marca isso explicitamente no
    nome; é uma escolha arbitrária mas REPRODUTÍVEL, que é o que importa
    para o manifesto de extração).
    """
    if estrategia != "primeiro_alfabetico":
        raise ValueError(f"estratégia desconhecida: {estrategia!r}")

    grupos: dict[str, list[Path]] = defaultdict(list)
    sem_padrao: list[Path] = []

    for caminho in caminhos:
        base = identificar_base_roboflow(caminho.name)
        if base is None:
            sem_padrao.append(caminho)
            continue
        grupos[base].append(caminho)

    mantidos: list[Path] = []
    descartados: list[Path] = []
    for base, membros in grupos.items():
        membros_ordenados = sorted(membros, key=lambda p: p.name)
        mantidos.append(membros_ordenados[0])
        descartados.extend(membros_ordenados[1:])

    return ResultadoDeduplicacao(
        mantidos=sorted(mantidos, key=lambda p: p.name),
        descartados=sorted(descartados, key=lambda p: p.name),
        sem_padrao_reconhecido=sorted(sem_padrao, key=lambda p: p.name),
    )

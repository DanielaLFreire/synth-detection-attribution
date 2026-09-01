"""
Colapso de múltiplas classes para classe única (tarefa -1.8, UA-DETRAC).

Diferente de materialize/labels_final.py (que VALIDA que só existe uma
classe, sem alterar nada), este módulo TRANSFORMA um label multi-classe em
classe única -- necessário porque o UA-DETRAC-DATASET-10K tem 4 classes
originais (bus, car, truck, van; ver docs/CHANGELOG_metodologico.md), e
este projeto trata veículo como classe única, mesmo tratamento já dado às
9 classes originais do CITRA-3D-Real.

Uso típico: colapsar_para_classe_unica(...) roda ANTES de
materializar_labels_final(...) -- o colapso produz a pasta de labels de
classe única que a materialização espera receber como
`labels_subfolder_origem`.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class ClasseOriginalInesperada(RuntimeError):
    """Levantado quando um label contém uma classe fora do conjunto
    declarado como válido -- evita colapsar silenciosamente uma classe que
    não foi conscientemente incluída na decisão de colapso."""


@dataclass
class RelatorioColapso:
    n_arquivos: int
    n_linhas: int
    contagem_por_classe_original: dict[str, int]


def colapsar_para_classe_unica(
    *,
    labels_origem_dir: Path,
    labels_destino_dir: Path,
    classes_originais_validas: set[str],
    classe_destino: str = "0",
) -> RelatorioColapso:
    """Reescreve cada label substituindo o id de classe original (que deve
    estar em `classes_originais_validas`) por `classe_destino`, preservando
    cx/cy/w/h inalterados. Não toca nas imagens -- só nos labels.
    """
    labels_origem_dir = Path(labels_origem_dir)
    labels_destino_dir = Path(labels_destino_dir)
    labels_destino_dir.mkdir(parents=True, exist_ok=True)

    n_arquivos = 0
    n_linhas = 0
    contagem: dict[str, int] = {c: 0 for c in classes_originais_validas}

    for caminho_origem in sorted(labels_origem_dir.glob("*.txt")):
        n_arquivos += 1
        linhas_novas = []
        with open(caminho_origem, "r", encoding="utf-8") as f:
            for linha in f:
                partes = linha.split()
                if not partes:
                    continue
                classe_original = partes[0]
                if classe_original not in classes_originais_validas:
                    raise ClasseOriginalInesperada(
                        f"{caminho_origem}: classe '{classe_original}' não está em "
                        f"classes_originais_validas={sorted(classes_originais_validas)} -- "
                        "colapso abortado. Se essa classe for legítima, inclua-a "
                        "explicitamente na decisão registrada, não silenciosamente."
                    )
                contagem[classe_original] += 1
                n_linhas += 1
                resto = partes[1:]
                linhas_novas.append(" ".join([classe_destino, *resto]))

        caminho_destino = labels_destino_dir / caminho_origem.name
        caminho_destino.write_text("\n".join(linhas_novas) + ("\n" if linhas_novas else ""), encoding="utf-8")

    return RelatorioColapso(n_arquivos=n_arquivos, n_linhas=n_linhas, contagem_por_classe_original=contagem)

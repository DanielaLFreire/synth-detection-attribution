"""
Perfilamento das fontes de crop (tarefa 0.2, §9 do plano).

Objetivo: decidir `min_dim_px` do filtro unificado (§8.1) com evidência --
não copiar um valor calibrado para uma fonte específica em outro projeto
(ver docs/CHANGELOG_metodologico.md sobre a decisão deliberada de não
fixar esse valor nas tarefas -1.3/-1.6).

Lê diretamente os manifestos de extração já gerados (largura_px, altura_px
por crop, por fonte) -- nenhum dado novo precisa ser calculado.
"""
from __future__ import annotations

import csv
from pathlib import Path


def _percentil(valores: list[float], p: float) -> float:
    if not valores:
        return float("nan")
    ordenados = sorted(valores)
    k = (len(ordenados) - 1) * (p / 100)
    f, c = int(k), min(int(k) + 1, len(ordenados) - 1)
    if f == c:
        return ordenados[f]
    return ordenados[f] + (ordenados[c] - ordenados[f]) * (k - f)


def perfilar_fonte(caminho_manifesto: Path, fonte: str) -> dict:
    """Lê um manifesto de extração e retorna estatísticas descritivas do
    menor lado de cada crop extraído com sucesso (extraido=True)."""
    menores_lados: list[int] = []

    with open(caminho_manifesto, newline="", encoding="utf-8") as f:
        for linha in csv.DictReader(f):
            if linha.get("extraido") != "True":
                continue
            largura = int(linha["largura_px"])
            altura = int(linha["altura_px"])
            menores_lados.append(min(largura, altura))

    if not menores_lados:
        return {"fonte": fonte, "n_crops": 0}

    valores_float = [float(v) for v in menores_lados]
    return {
        "fonte": fonte,
        "n_crops": len(menores_lados),
        "menor_lado_mediana": _percentil(valores_float, 50),
        "menor_lado_p5": _percentil(valores_float, 5),
        "menor_lado_p10": _percentil(valores_float, 10),
        "menor_lado_p25": _percentil(valores_float, 25),
        "menor_lado_min": min(menores_lados),
        "menor_lado_max": max(menores_lados),
        "_menores_lados": menores_lados,  # uso interno, não exibir em relatório resumido
    }


def tabela_decisao_min_dim_px(
    perfis: list[dict], candidatos: list[int],
) -> list[dict]:
    """Para cada fonte perfilada e cada limiar candidato, calcula quantos
    crops sobrariam (contagem e % do total daquela fonte) -- a tabela que
    sustenta a decisão do valor final de min_dim_px, em vez de escolher um
    número sem ver o custo de cada fonte."""
    linhas = []
    for perfil in perfis:
        if perfil["n_crops"] == 0:
            continue
        menores_lados = perfil["_menores_lados"]
        linha = {"fonte": perfil["fonte"], "n_crops_total": perfil["n_crops"]}
        for limiar in candidatos:
            n_mantidos = sum(1 for m in menores_lados if m >= limiar)
            linha[f"mantidos_em_{limiar}px"] = n_mantidos
            linha[f"pct_mantidos_em_{limiar}px"] = round(100 * n_mantidos / perfil["n_crops"], 1)
        linhas.append(linha)
    return linhas

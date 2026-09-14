"""
Montador da tabela de features do Estágio A (CPU).

Junta, numa única tabela (uma linha por colagem):
- todas as colunas do alvo (que já carregam o manifesto de composição);
- features de geometria/transformação (calcular_features_geometricas);
- coerência escala x posição (resíduo da regressão ajustada nas caixas
  REAIS do alvo -- split de validação, o mesmo sobre o qual as colagens
  foram feitas);
- features intrínsecas do crop (nitidez, contraste, brilho, cobertura),
  calculadas UMA vez por crop único e reaproveitadas -- as 25.340 colagens
  usam crops com reposição de um pool de ~86 mil, então muitos se repetem.

Nenhuma GPU. Nenhuma feature baseada em CLIP ainda (decisão de
2026-09-14: avaliar o modelo com estas antes de investir em CLIP).
"""
from __future__ import annotations

import csv
from pathlib import Path

from .features import (
    calcular_features_geometricas,
    ajustar_regressao_escala_posicao,
    caixas_reais_do_alvo,
    calcular_features_intrinsecas,
)

COLUNAS_INTRINSECAS = ("nitidez", "contraste", "brilho_medio", "cobertura_mascara")


def _localizar_crop(caminho_registrado: str, indice_crops: dict[str, Path]) -> Path | None:
    """O manifesto registra o caminho local de quando a composição rodou
    (que não existe mais). Localiza o arquivo pelo nome-base num índice
    construído a partir dos zips de crop extraídos localmente agora."""
    return indice_crops.get(Path(caminho_registrado).name)


def construir_tabela_features(
    alvo_csv: Path,
    labels_reais_alvo_dir: Path,
    indice_crops: dict[str, Path],
    destino_csv: Path,
) -> dict:
    """Escreve a tabela de features e retorna um resumo (contagens,
    quantos crops não foram localizados, coeficientes da regressão)."""
    pos_v_reais, area_reais = caixas_reais_do_alvo(labels_reais_alvo_dir)
    regressao = ajustar_regressao_escala_posicao(pos_v_reais, area_reais)

    cache_intrinsecas: dict[str, dict] = {}
    n_linhas = 0
    n_crop_nao_localizado = 0

    destino_csv = Path(destino_csv)
    destino_csv.parent.mkdir(parents=True, exist_ok=True)

    with open(alvo_csv, newline="", encoding="utf-8") as f_in, \
         open(destino_csv, "w", newline="", encoding="utf-8") as f_out:
        reader = csv.DictReader(f_in)
        primeira = True
        writer = None

        for linha in reader:
            geo = calcular_features_geometricas(linha)
            geo["coerencia_escala_pos"] = regressao.residuo(geo["pos_v"], geo["area_caixa_norm"])

            nome_crop = Path(linha["crop_path"]).name
            if nome_crop not in cache_intrinsecas:
                caminho = _localizar_crop(linha["crop_path"], indice_crops)
                if caminho is None:
                    cache_intrinsecas[nome_crop] = {c: "" for c in COLUNAS_INTRINSECAS}
                    n_crop_nao_localizado += 1
                else:
                    cache_intrinsecas[nome_crop] = calcular_features_intrinsecas(caminho)
            intr = cache_intrinsecas[nome_crop]

            saida = dict(linha)
            saida.update(geo)
            saida.update({c: intr.get(c, "") for c in COLUNAS_INTRINSECAS})

            if primeira:
                writer = csv.DictWriter(f_out, fieldnames=list(saida.keys()))
                writer.writeheader()
                primeira = False
            writer.writerow(saida)
            n_linhas += 1

    return {
        "n_linhas": n_linhas,
        "n_crops_unicos": len(cache_intrinsecas),
        "n_crops_nao_localizados": n_crop_nao_localizado,
        "regressao_coerencia": {"a": regressao.a, "b": regressao.b},
        "n_caixas_reais_usadas_na_regressao": len(pos_v_reais),
    }


def construir_indice_crops(pastas_crops: list[Path]) -> dict[str, Path]:
    """Indexa todos os arquivos de crop (extraídos localmente dos zips das
    fontes) por nome-base: {nome_arquivo: caminho}."""
    indice: dict[str, Path] = {}
    for pasta in pastas_crops:
        for caminho in Path(pasta).iterdir():
            if caminho.is_file():
                indice[caminho.name] = caminho
    return indice

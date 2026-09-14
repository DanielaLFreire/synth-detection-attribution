"""
Script de entrada para a Fase 2 (Estágio A): análise SHAP sobre o modelo
substituto que passou o portão -- ranking, direção, clusters, e
estabilidade por bootstrap por grupo. Nenhuma GPU.

ATENÇÃO: rodar numa sessão SEM `sam3` instalado (conflito numpy<2 vs >=2).

Uso no Colab:

    import sys
    sys.path.insert(0, "/content/synth-detection-attribution")
    from scripts.analisar_shap_estagio_a import main

    saida = main()
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.attribution import (
    treinar_modelo_final, calcular_shap, ranking_importancia, importancia_por_cluster,
    estabilidade_bootstrap_por_grupo, FEATURES_PRINCIPAIS,
)

RAIZ = "/content/drive/MyDrive/PROJETO_MARINHA/EXPERIMENTO_ATRIBUICAO_CAUSAL/estagio_a"
TABELA = f"{RAIZ}/features/tabela_features_estagio_a.csv"
DESTINO = f"{RAIZ}/shap"


def main(tabela_csv: str = TABELA, destino: str = DESTINO, n_reamostras: int = 30, k: int = 5) -> dict:
    df = pd.read_csv(tabela_csv)
    print(f"Tabela: {len(df)} linhas, {df['grupo_geometrico_id'].nunique()} grupos\n")

    print("1) Modelo final em todos os dados + SHAP...")
    modelo = treinar_modelo_final(df)
    X = df[FEATURES_PRINCIPAIS].to_numpy(dtype=float)
    sv = calcular_shap(modelo, X)
    rk = ranking_importancia(sv, X, FEATURES_PRINCIPAIS)

    print("\n=== RANKING POR FEATURE (|SHAP| médio; direção: +1 = maior valor -> mais acerto) ===")
    for _, r in rk.iterrows():
        print(f"  {int(r['posicao']):>2}. {r['feature']:<30} imp={r['importancia_shap']:.4f}  direcao={r['direcao']:+.2f}")

    por_cluster = importancia_por_cluster(rk)
    print("\n=== RANKING POR CLUSTER (§5.5) ===")
    for _, r in por_cluster.iterrows():
        print(f"  {int(r['posicao']):>2}. {r['cluster']:<30} imp={r['importancia_shap']:.4f}  {r['features']}")

    print(f"\n2) Estabilidade por bootstrap POR GRUPO ({n_reamostras} reamostras, top-{k})...")
    est = estabilidade_bootstrap_por_grupo(df, n_reamostras=n_reamostras, k=k)
    print(f"\n=== ESTABILIDADE (posição média ± desvio; frequência no top-{k}) ===")
    for f in rk["feature"]:
        print(f"  {f:<30} pos={est.posicao_media[f]:>5.2f} ± {est.posicao_desvio[f]:>4.2f}   "
              f"top-{k}: {100*est.frequencia_top_k[f]:>5.1f}%")

    saida = {
        "ranking": rk.to_dict(orient="records"),
        "ranking_por_cluster": por_cluster.to_dict(orient="records"),
        "estabilidade": {
            "n_reamostras": est.n_reamostras, "k": est.k,
            "posicao_media": est.posicao_media, "posicao_desvio": est.posicao_desvio,
            "frequencia_top_k": est.frequencia_top_k,
        },
    }
    Path(destino).mkdir(parents=True, exist_ok=True)
    (Path(destino) / "shap_estagio_a.json").write_text(json.dumps(saida, indent=2, default=str), encoding="utf-8")
    print(f"\nResultado salvo em {Path(destino) / 'shap_estagio_a.json'}")
    return saida


if __name__ == "__main__":
    main()

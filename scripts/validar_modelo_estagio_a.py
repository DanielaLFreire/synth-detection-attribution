"""
Script de entrada para a Fase 2 (Estágio A): validação cruzada por grupo
do modelo substituto sobre a tabela de features real, com o portão
pré-registrado de AUC-PR >= 0,78. Nenhuma GPU.

Uso no Colab:

    import sys
    sys.path.insert(0, "/content/synth-detection-attribution")
    from scripts.validar_modelo_estagio_a import main

    resultado = main()
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.attribution import validar_por_grupo, FEATURES_PRINCIPAIS, PISO_AUC_PR

RAIZ = "/content/drive/MyDrive/PROJETO_MARINHA/EXPERIMENTO_ATRIBUICAO_CAUSAL/estagio_a"
TABELA = f"{RAIZ}/features/tabela_features_estagio_a.csv"
DESTINO = f"{RAIZ}/modelo"


def main(tabela_csv: str = TABELA, destino: str = DESTINO, n_folds: int = 5) -> dict:
    df = pd.read_csv(tabela_csv)
    print(f"Tabela: {len(df)} linhas, {df['grupo_geometrico_id'].nunique()} grupos geométricos")
    print(f"Taxa base (acerto_votacao): {df['acerto_votacao'].mean():.3f}")
    print(f"Features ({len(FEATURES_PRINCIPAIS)}): {FEATURES_PRINCIPAIS}")
    print(f"Piso pré-registrado do portão: AUC-PR >= {PISO_AUC_PR}\n")

    r = validar_por_grupo(df, n_folds=n_folds)

    print(f"AUC-PR por fold:  {[round(v, 4) for v in r.auc_pr_por_fold]}")
    print(f"AUC-PR média:     {r.auc_pr_media:.4f}  (desvio {r.auc_pr_desvio:.4f})")
    print(f"AUC-ROC média:    {r.auc_roc_media:.4f}")
    print(f"Ganho sobre a taxa base: {r.auc_pr_media - r.taxa_base:+.4f}")
    print(f"\nPORTÃO: {'✅ PASSOU' if r.passou_portao else '❌ NÃO PASSOU'} "
          f"(média {r.auc_pr_media:.4f} vs piso {r.piso})")

    saida = {
        "n_linhas": int(len(df)),
        "n_grupos": int(df["grupo_geometrico_id"].nunique()),
        "taxa_base": r.taxa_base,
        "features": FEATURES_PRINCIPAIS,
        "n_folds": r.n_folds,
        "auc_pr_por_fold": r.auc_pr_por_fold,
        "auc_pr_media": r.auc_pr_media,
        "auc_pr_desvio": r.auc_pr_desvio,
        "auc_roc_media": r.auc_roc_media,
        "piso": r.piso,
        "passou_portao": r.passou_portao,
    }
    Path(destino).mkdir(parents=True, exist_ok=True)
    (Path(destino) / "validacao_por_grupo.json").write_text(json.dumps(saida, indent=2), encoding="utf-8")
    print(f"\nResultado salvo em {Path(destino) / 'validacao_por_grupo.json'}")
    return saida


if __name__ == "__main__":
    main()

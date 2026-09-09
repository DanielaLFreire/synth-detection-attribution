"""
Script de entrada para a tarefa 0.2: perfila as quatro fontes de crop a
partir dos manifestos de extração já gerados, e monta a tabela de decisão
de `min_dim_px`.

Uso no Colab:

    import sys
    sys.path.insert(0, "/content/synth-detection-attribution")
    from scripts.perfilar_fontes import main

    main()  # usa os caminhos padrão do Drive; ajuste se necessário
"""
from __future__ import annotations

import json
from pathlib import Path

from src.profiling import perfilar_fonte, tabela_decisao_min_dim_px

RAIZ_CROPS = "/content/drive/MyDrive/PROJETO_MARINHA/EXPERIMENTO_ATRIBUICAO_CAUSAL/crops_sam3"

MANIFESTOS_PADRAO = {
    "SMD": f"{RAIZ_CROPS}/manifesto_extracao_bruta_smd.csv",
    "SeaShips": f"{RAIZ_CROPS}/manifesto_extracao_bruta_seaships.csv",
    "ABOShips": f"{RAIZ_CROPS}/manifesto_extracao_bruta_aboships.csv",
    "InaTechShips": [
        f"{RAIZ_CROPS}/manifesto_extracao_bruta_inatechships_train.csv",
        f"{RAIZ_CROPS}/manifesto_extracao_bruta_inatechships_val.csv",
        f"{RAIZ_CROPS}/manifesto_extracao_bruta_inatechships_test.csv",
    ],
}

CANDIDATOS_PADRAO = [8, 12, 16, 20, 24, 32, 40, 48]


def main(
    manifestos: dict[str, str] | None = None,
    candidatos: list[int] | None = None,
    destino_json: str | None = None,
) -> list[dict]:
    manifestos = manifestos or MANIFESTOS_PADRAO
    candidatos = candidatos or CANDIDATOS_PADRAO

    perfis = []
    print("Perfilando fontes a partir dos manifestos de extração...\n")
    for fonte, caminho in manifestos.items():
        caminho_normalizado = [Path(c) for c in caminho] if isinstance(caminho, list) else Path(caminho)
        perfil = perfilar_fonte(caminho_normalizado, fonte=fonte)
        perfis.append(perfil)
        if perfil["n_crops"] == 0:
            print(f"  {fonte}: manifesto vazio ou não encontrado -- ignorado.")
            continue
        print(f"  {fonte}: {perfil['n_crops']} crops -- menor lado: "
              f"mediana={perfil['menor_lado_mediana']:.0f}px, "
              f"p5={perfil['menor_lado_p5']:.0f}px, "
              f"min={perfil['menor_lado_min']}px, max={perfil['menor_lado_max']}px")

    tabela = tabela_decisao_min_dim_px(perfis, candidatos)

    print("\n" + "=" * 100)
    print("Tabela de decisão -- % de crops mantidos por fonte, em cada limiar candidato")
    print("=" * 100)
    cabecalho = f"{'Fonte':<12}{'N total':>10}" + "".join(f"{f'>={c}px':>10}" for c in candidatos)
    print(cabecalho)
    for linha in tabela:
        valores = "".join(f"{linha[f'pct_mantidos_em_{c}px']:>9.1f}%" for c in candidatos)
        print(f"{linha['fonte']:<12}{linha['n_crops_total']:>10}{valores}")

    if destino_json:
        Path(destino_json).parent.mkdir(parents=True, exist_ok=True)
        Path(destino_json).write_text(
            json.dumps({"perfis": [{k: v for k, v in p.items() if not k.startswith("_")} for p in perfis],
                        "tabela_decisao": tabela}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"\nResultado salvo em {destino_json}")

    return tabela


if __name__ == "__main__":
    main()

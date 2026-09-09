"""
Script de entrada para a tarefa 0.3: verifica se cada fonte tem
reservatório suficiente para contribuir, em proporção comparável às
outras, a cada nível do fator "compatibilidade de escala" do Estágio B.

Usa os tamanhos REAIS das caixas do CITRA-3D-Real (split de treino, maior
amostra disponível da distribuição de tamanho do alvo) como destino, e os
tamanhos reais dos crops que passaram o filtro de qualidade
(`min_dim_px=20`, tarefa 0.2) como origem, por fonte.

Uso no Colab:

    import sys
    sys.path.insert(0, "/content/synth-detection-attribution")
    from scripts.verificar_cobertura_fatorial import main

    main()
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from src.profiling import obter_tamanhos_absolutos_alvo, simular_compatibilidade_escala

CITRA_IMAGENS_DIR = "/content/drive/MyDrive/PROJETO_MARINHA/Datasets/CITRA-3D-Real/train/images"
CITRA_LABELS_DIR = "/content/drive/MyDrive/PROJETO_MARINHA/Datasets/CITRA-3D-Real/train/labels_final"

RAIZ_CROPS = "/content/drive/MyDrive/PROJETO_MARINHA/EXPERIMENTO_ATRIBUICAO_CAUSAL/crops_sam3"

MANIFESTOS_FILTRO_PADRAO = {
    "SMD": f"{RAIZ_CROPS}/manifesto_filtro_qualidade_smd.csv",
    "SeaShips": f"{RAIZ_CROPS}/manifesto_filtro_qualidade_seaships.csv",
    "ABOShips": f"{RAIZ_CROPS}/manifesto_filtro_qualidade_aboships.csv",
    "InaTechShips": f"{RAIZ_CROPS}/manifesto_filtro_qualidade_inatechships.csv",
}


def _tamanhos_mantidos_do_manifesto_filtro(caminho: Path) -> list[tuple[int, int]]:
    tamanhos = []
    with open(caminho, newline="", encoding="utf-8") as f:
        for linha in csv.DictReader(f):
            if linha.get("mantido") == "True":
                tamanhos.append((int(linha["largura_px"]), int(linha["altura_px"])))
    return tamanhos


def main(
    citra_imagens_dir: str = CITRA_IMAGENS_DIR,
    citra_labels_dir: str = CITRA_LABELS_DIR,
    manifestos_filtro: dict[str, str] | None = None,
    n_amostras: int = 20000,
    faixa_casada: tuple[float, float] = (0.5, 2.0),
    destino_json: str | None = None,
) -> list[dict]:
    manifestos_filtro = manifestos_filtro or MANIFESTOS_FILTRO_PADRAO

    print(f"Lendo tamanhos reais de caixas do CITRA-3D-Real (train)...")
    tamanhos_destino = obter_tamanhos_absolutos_alvo(Path(citra_imagens_dir), Path(citra_labels_dir))
    print(f"  {len(tamanhos_destino)} caixas de destino carregadas.\n")

    resultados = []
    print(f"Simulando compatibilidade de escala (faixa 'casada' = {faixa_casada}, "
          f"{n_amostras} amostras por fonte)...\n")
    for fonte, caminho in manifestos_filtro.items():
        tamanhos_origem = _tamanhos_mantidos_do_manifesto_filtro(Path(caminho))
        resultado = simular_compatibilidade_escala(
            fonte=fonte, tamanhos_origem=tamanhos_origem, tamanhos_destino=tamanhos_destino,
            n_amostras=n_amostras, faixa_casada=faixa_casada,
        )
        resultados.append(resultado)
        print(f"  {fonte} (n_origem={len(tamanhos_origem)}): "
              f"casada={resultado.pct_casada:.1f}%  "
              f"descasada_downscale={resultado.pct_descasada_downscale:.1f}%  "
              f"descasada_upscale={resultado.pct_descasada_upscale:.1f}%")

    print("\n" + "=" * 70)
    print("Leitura: se 'casada' for muito próximo de 0% para alguma fonte,")
    print("essa fonte não tem reservatório para contribuir à célula 'casada'")
    print("na mesma proporção que as outras -- risco de confound de fonte")
    print("no fatorial do Estágio B, a resolver antes da Fase 3.")
    print("=" * 70)

    if destino_json:
        Path(destino_json).parent.mkdir(parents=True, exist_ok=True)
        Path(destino_json).write_text(
            json.dumps([vars(r) for r in resultados], indent=2, ensure_ascii=False), encoding="utf-8",
        )
        print(f"\nResultado salvo em {destino_json}")

    return [vars(r) for r in resultados]


if __name__ == "__main__":
    main()

"""
Script de entrada para a tarefa 0.4: gera as colagens de sondagem do
Estágio A sobre o split de VALIDAÇÃO do CITRA-3D-Real (nunca o de treino
-- decisão registrada em §5.2 do plano, para evitar o confound de
memorização de cena).

Combina o pool de crops das quatro fontes (SMD, SeaShips, ABOShips,
InaTechShips), já segmentadas com SAM 3 e filtradas em min_dim_px=20,
extraindo cada zip para uma pasta local temporária antes de montar o
pool_crops combinado -- nenhuma mudança no componente de composição
(`src.compose.compor_dataset`) foi necessária.

Uso no Colab:

    import sys
    sys.path.insert(0, "/content/synth-detection-attribution")
    from scripts.gerar_colagens_sondagem import main

    main()  # usa os caminhos padrão do Drive; ajuste se necessário
"""
from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

from src.compose import compor_dataset
from src.extraction import carregar_pool_de_crops_do_zip

RAIZ_CROPS = "/content/drive/MyDrive/PROJETO_MARINHA/EXPERIMENTO_ATRIBUICAO_CAUSAL/crops_sam3"
CITRA_VAL_IMAGENS = "/content/drive/MyDrive/PROJETO_MARINHA/Datasets/CITRA-3D-Real/val/images"
CITRA_VAL_LABELS = "/content/drive/MyDrive/PROJETO_MARINHA/Datasets/CITRA-3D-Real/val/labels_final"
DESTINO_DRIVE = "/content/drive/MyDrive/PROJETO_MARINHA/EXPERIMENTO_ATRIBUICAO_CAUSAL/estagio_a/colagens_sondagem_val"

ZIPS_FONTES = {
    "SMD": f"{RAIZ_CROPS}/smd.zip",
    "SeaShips": f"{RAIZ_CROPS}/seaships.zip",
    "ABOShips": f"{RAIZ_CROPS}/aboships.zip",
    "InaTechShips": f"{RAIZ_CROPS}/inatechships.zip",
}


def main(
    destino_extracao_local: str = "/content/colagens_sondagem_local",
    destino_drive: str = DESTINO_DRIVE,
    zips_fontes: dict[str, str] | None = None,
    citra_val_imagens: str = CITRA_VAL_IMAGENS,
    citra_val_labels: str = CITRA_VAL_LABELS,
    n_variacoes: int = 20,
    seed: int = 42,
) -> int:
    """
    `n_variacoes=20` -- decisão corrigida em 2026-09-02 (ver
    docs/CHANGELOG_metodologico.md). NÃO herda o valor 13 do projeto
    anterior: aquele número foi escolhido para equilibrar volume real vs.
    sintético 50/50 num braço de treino supervisionado com GPU -- um
    problema que não existe aqui (nenhum treino acontece sobre estas
    colagens). 20 foi escolhido por raciocínio próprio deste contexto:
    sem custo de GPU na composição, mais variações por grupo geométrico
    (imagem, caixa) dão mais resolução ao GBM+SHAP do Estágio A para
    aprender o efeito do crop com a geometria controlada. Não é um valor
    otimizado por análise de poder formal -- revisável se a modelagem do
    Estágio A (Fase 2) mostrar sinal insuficiente por falta de variação
    dentro de grupo.
    """
    zips_fontes = zips_fontes or ZIPS_FONTES
    destino_extracao_local = Path(destino_extracao_local)
    destino_drive = Path(destino_drive)

    print("1) Extraindo os zips de crop das quatro fontes para pastas locais temporárias...")
    pool_crops = []
    for fonte, caminho_zip in zips_fontes.items():
        destino_local_fonte = destino_extracao_local / "pool" / fonte.lower()
        pool_fonte = carregar_pool_de_crops_do_zip(Path(caminho_zip), fonte=fonte, destino_local=destino_local_fonte)
        pool_crops.extend(pool_fonte)
        print(f"   {fonte}: {len(pool_fonte)} crops carregados.")
    print(f"   Pool combinado: {len(pool_crops)} crops de {len(zips_fontes)} fontes.\n")

    saida_imagens = destino_extracao_local / "colagens" / "images"
    saida_labels = destino_extracao_local / "colagens" / "labels"
    manifesto_csv = destino_extracao_local / "manifesto_colagens_sondagem_val.csv"
    manifesto_meta = destino_extracao_local / "manifesto_colagens_sondagem_val_meta.json"

    print(f"2) Compondo colagens de sondagem sobre o split de VALIDAÇÃO do CITRA-3D-Real "
          f"(n_variacoes={n_variacoes}, seed={seed})...")
    n_colagens = compor_dataset(
        imagens_alvo_dir=Path(citra_val_imagens),
        labels_alvo_dir=Path(citra_val_labels),
        pool_crops=pool_crops,
        saida_imagens_dir=saida_imagens,
        saida_labels_dir=saida_labels,
        manifesto_csv=manifesto_csv,
        manifesto_metadata_json=manifesto_meta,
        split="val",
        n_variacoes=n_variacoes,
        seed=seed,
    )
    print(f"   {n_colagens} colagens geradas (linhas de manifesto).\n")

    print(f"3) Compactando imagens e labels gerados, copiando para o Drive ({destino_drive})...")
    destino_drive.mkdir(parents=True, exist_ok=True)

    zip_imagens = destino_extracao_local / "colagens_images.zip"
    with zipfile.ZipFile(zip_imagens, "w", zipfile.ZIP_DEFLATED) as zf:
        for caminho in sorted(saida_imagens.glob("*.png")):
            zf.write(caminho, arcname=caminho.name)
    shutil.copy2(zip_imagens, destino_drive / "colagens_images.zip")

    zip_labels = destino_extracao_local / "colagens_labels.zip"
    with zipfile.ZipFile(zip_labels, "w", zipfile.ZIP_DEFLATED) as zf:
        for caminho in sorted(saida_labels.glob("*.txt")):
            zf.write(caminho, arcname=caminho.name)
    shutil.copy2(zip_labels, destino_drive / "colagens_labels.zip")

    shutil.copy2(manifesto_csv, destino_drive / manifesto_csv.name)
    shutil.copy2(manifesto_meta, destino_drive / manifesto_meta.name)

    print(f"\n✅ Concluído. {n_colagens} colagens de sondagem geradas sobre o split de validação.")
    print(f"   Imagens: {destino_drive / 'colagens_images.zip'}")
    print(f"   Labels: {destino_drive / 'colagens_labels.zip'}")
    print(f"   Manifesto: {destino_drive / manifesto_csv.name}")

    return n_colagens


if __name__ == "__main__":
    main()

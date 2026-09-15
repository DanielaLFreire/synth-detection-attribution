"""
Tarefa 3.2 (parte 2) -- gera as 4 células do fatorial 2 × 2 (adendo 2,
commit a4ec7ab). CPU pura.

Para cada célula (escala × contraste):
1. Constrói o seletor com o pool elegível (contraste cacheado), a mediana
   e a lista PRÉ-REGISTRADA de caixas viáveis (configs/caixas_viaveis_fase3.csv).
2. Compõe sobre o split de TREINO (override explícito, justificado no
   adendo 2 §3), n_variacoes=2, seed fixa por célula.
3. Verifica o manifesto contra o adendo: todo crop no nível de escala e
   de contraste certos; proporção de fonte; conjunto de caixas coladas
   IDÊNTICO entre células; distribuição de fator_reescala (adendo 2 §2).
4. Compacta imagens+labels num zip por célula (evita OSError FUSE) e
   copia com o manifesto para o Drive.

Uso no Colab (CPU):

    import sys
    sys.path.insert(0, "/content/synth-detection-attribution")
    from scripts.gerar_celulas_fase3 import main

    main()
"""
from __future__ import annotations

import csv
import json
import shutil
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from src.compose.compose import compor_dataset
from src.factorial import (
    CropElegivel, construir_seletor_celula, carregar_caixas_permitidas, nivel_escala, nivel_contraste,
    FONTES_ELEGIVEIS,
)

RAIZ = "/content/drive/MyDrive/PROJETO_MARINHA/EXPERIMENTO_ATRIBUICAO_CAUSAL"
ZIPS_CROPS = {
    "SMD": f"{RAIZ}/crops_sam3/smd.zip",
    "SeaShips": f"{RAIZ}/crops_sam3/seaships.zip",
    "ABOShips": f"{RAIZ}/crops_sam3/aboships.zip",
}
CACHE_CONTRASTE = f"{RAIZ}/fase3/contraste_pool_elegivel.csv"
REAL_TRAIN_IMAGES = "/content/drive/MyDrive/PROJETO_MARINHA/Datasets/CITRA-3D-Real/train/images"
REAL_TRAIN_LABELS = "/content/drive/MyDrive/PROJETO_MARINHA/Datasets/CITRA-3D-Real/train/labels_final"
DESTINO_DRIVE = f"{RAIZ}/fase3/celulas"

CELULAS = [("casada", "alto"), ("casada", "baixo"), ("reduzida", "alto"), ("reduzida", "baixo")]
SEEDS_CELULA = {"casada__alto": 3101, "casada__baixo": 3102, "reduzida__alto": 3103, "reduzida__baixo": 3104}
N_VARIACOES = 2
MINIMO_POR_FONTE = 2


def _carregar_pool(cache: Path) -> list[CropElegivel]:
    with open(cache, newline="", encoding="utf-8") as f:
        return [CropElegivel(l["nome"], l["fonte"], float(int(l["largura"]) * int(l["altura"])), float(l["contraste"]))
                for l in csv.DictReader(f)]


def _extrair_crops(zips: dict, destino: Path) -> dict[str, Path]:
    caminhos = {}
    for fonte, z in zips.items():
        pasta = destino / fonte
        pasta.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(z) as zf:
            zf.extractall(pasta)
        for p in pasta.iterdir():
            if p.is_file():
                caminhos[p.name] = p
    return caminhos


def _verificar_manifesto(manifesto: Path, escala: str, contraste_celula: str, contraste_por_nome: dict[str, float],
                         mediana: float) -> dict:
    linhas = list(csv.DictReader(open(manifesto, newline="", encoding="utf-8")))
    fatores = np.array([float(l["fator_reescala"]) for l in linhas])
    erros_escala = int(sum(nivel_escala(f) != escala for f in fatores))
    erros_contraste = int(sum(
        nivel_contraste(contraste_por_nome[Path(l["crop_path"]).name], mediana) != contraste_celula for l in linhas))
    fontes = Counter(l["fonte"] for l in linhas)
    caixas = {(l["imagem_id"], int(l["box_index"])) for l in linhas}
    return {
        "n_colagens": len(linhas),
        "n_caixas_coladas_distintas": len(caixas),
        "erros_nivel_escala": erros_escala,
        "erros_nivel_contraste": erros_contraste,
        "proporcao_fonte": {f: fontes[f] / len(linhas) for f in FONTES_ELEGIVEIS} if linhas else {},
        "fator_reescala": {"min": float(fatores.min()), "p05": float(np.percentile(fatores, 5)),
                           "mediana": float(np.median(fatores)), "p95": float(np.percentile(fatores, 95)),
                           "max": float(fatores.max())} if len(fatores) else {},
        "_caixas": caixas,
    }


def main(
    destino_local: str = "/content/fase3_celulas_local",
    destino_drive: str = DESTINO_DRIVE,
    cache_contraste: str = CACHE_CONTRASTE,
    caixas_viaveis_csv: str = "configs/caixas_viaveis_fase3.csv",
    celulas_json: str = "configs/celulas_fase3.json",
    real_train_images: str = REAL_TRAIN_IMAGES,
    real_train_labels: str = REAL_TRAIN_LABELS,
    celulas: list[tuple[str, str]] | None = None,
) -> dict:
    celulas = celulas or CELULAS
    destino_local = Path(destino_local); destino_drive = Path(destino_drive)
    destino_drive.mkdir(parents=True, exist_ok=True)

    cfg = json.loads(Path(celulas_json).read_text(encoding="utf-8"))
    mediana = float(cfg["mediana_contraste"])
    assert cfg["minimo_por_fonte"] == MINIMO_POR_FONTE and cfg["niveis_escala"] == ["casada", "reduzida"], \
        "configs/celulas_fase3.json não é o do adendo 2 (2x2, min2)"
    print(f"mediana de contraste (config lacrada): {mediana:.5f}")

    print("1) Pool elegível e crops locais...")
    pool = _carregar_pool(Path(cache_contraste))
    contraste_por_nome = {c.nome: c.contraste for c in pool}
    caminhos = _extrair_crops(ZIPS_CROPS, destino_local / "crops")
    permitidas = carregar_caixas_permitidas(Path(caixas_viaveis_csv))
    print(f"   {len(pool)} crops no pool, {len(caminhos)} arquivos, {len(permitidas)} caixas permitidas\n")

    resumo = {"gerado_em_utc": datetime.now(timezone.utc).isoformat(), "adendo": "adendo2 (a4ec7ab)",
              "n_variacoes": N_VARIACOES, "mediana_contraste": mediana, "celulas": {}}
    conjuntos_caixas = {}

    for escala, contraste in celulas:
        nome = f"{escala}__{contraste}"
        print(f"2) Célula {nome} (seed {SEEDS_CELULA[nome]})...")
        pasta = destino_local / nome
        seletor = construir_seletor_celula(pool, caminhos, mediana, escala, contraste, permitidas, MINIMO_POR_FONTE)
        n = compor_dataset(
            imagens_alvo_dir=Path(real_train_images), labels_alvo_dir=Path(real_train_labels), pool_crops=[],
            saida_imagens_dir=pasta / "images", saida_labels_dir=pasta / "labels",
            manifesto_csv=pasta / f"manifesto_{nome}.csv", manifesto_metadata_json=pasta / f"metadata_{nome}.json",
            split="train", n_variacoes=N_VARIACOES, seed=SEEDS_CELULA[nome], permitir_split_treino=True,
            seletor_de_crop=seletor,
        )
        v = _verificar_manifesto(pasta / f"manifesto_{nome}.csv", escala, contraste, contraste_por_nome, mediana)
        conjuntos_caixas[nome] = v.pop("_caixas")
        v["n_colagens_compor_dataset"] = n
        v["seed"] = SEEDS_CELULA[nome]
        resumo["celulas"][nome] = v
        print(f"   {n} colagens | caixas distintas {v['n_caixas_coladas_distintas']} | "
              f"erros escala {v['erros_nivel_escala']} | erros contraste {v['erros_nivel_contraste']} | "
              f"fontes {{{', '.join(f'{k}: {p:.3f}' for k, p in v['proporcao_fonte'].items())}}}")
        print(f"   fator_reescala: p05={v['fator_reescala']['p05']:.3f} mediana={v['fator_reescala']['mediana']:.3f} "
              f"p95={v['fator_reescala']['p95']:.3f}")

        # zip único por célula (imagens + labels), depois manifesto/metadata
        zip_path = destino_local / f"{nome}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_STORED) as zf:
            for sub in ("images", "labels"):
                for p in sorted((pasta / sub).iterdir()):
                    zf.write(p, f"{sub}/{p.name}")
        shutil.copy2(zip_path, destino_drive / zip_path.name)
        shutil.copy2(pasta / f"manifesto_{nome}.csv", destino_drive / f"manifesto_{nome}.csv")
        shutil.copy2(pasta / f"metadata_{nome}.json", destino_drive / f"metadata_{nome}.json")
        print(f"   copiado para o Drive: {zip_path.name}\n")

    # 3) mesmas caixas em todas as células (adendo 2 §3.1)
    nomes = list(conjuntos_caixas)
    identicos = all(conjuntos_caixas[n] == conjuntos_caixas[nomes[0]] for n in nomes)
    iguais_as_permitidas = conjuntos_caixas[nomes[0]] == permitidas
    resumo["mesmas_caixas_em_todas_as_celulas"] = identicos
    resumo["caixas_coladas_iguais_as_pre_registradas"] = iguais_as_permitidas
    print(f"3) Mesmas caixas em todas as células: {'✅' if identicos else '❌'} | "
          f"iguais às pré-registradas: {'✅' if iguais_as_permitidas else '❌'}")

    (destino_drive / "resumo_celulas_fase3.json").write_text(json.dumps(resumo, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n✅ Resumo salvo em {destino_drive / 'resumo_celulas_fase3.json'}")
    return resumo


if __name__ == "__main__":
    main()

"""
Fase 3 -- prepara os dados locais para o treino do fatorial 2 × 2
(adendo 2, commit a4ec7ab). CPU.

- Copia real train/val do CITRA para disco local.
- Extrai o zip de cada célula (images/ + labels/).
- Monta as trainlists: cada célula = real × repeat_real(2) + sintéticas
  da célula (~51/49); controle = real × 2, zero sintético.
- Grava data_{braço}.yaml e `contagens.json` (imagens por época por braço,
  lido pelo treino -- nunca codificado à mão).

Uso no Colab:

    import sys
    sys.path.insert(0, "/content/synth-detection-attribution")
    from scripts.preparar_dados_locais_fase3 import main

    main()
"""
from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path

from src.train import construir_trainlist_balanceado, construir_trainlist_real_sobreamostrado

RAIZ = "/content/drive/MyDrive/PROJETO_MARINHA/EXPERIMENTO_ATRIBUICAO_CAUSAL"
DRIVE_CELULAS = f"{RAIZ}/fase3/celulas"
CITRA = "/content/drive/MyDrive/PROJETO_MARINHA/Datasets/CITRA-3D-Real"
CELULAS = ["casada__alto", "casada__baixo", "reduzida__alto", "reduzida__baixo"]
REPEAT_REAL = 2  # = n_variacoes (adendo 2 §3.5-6)


def _copiar_pasta(origem: Path, destino: Path) -> int:
    destino.mkdir(parents=True, exist_ok=True)
    n = 0
    for p in Path(origem).iterdir():
        if p.is_file():
            shutil.copy2(p, destino / p.name); n += 1
    return n


def _yaml(caminho: Path, train_txt: Path, val_dir: Path) -> None:
    caminho.write_text(f"train: {train_txt}\nval: {val_dir}\nnc: 1\nnames:\n  - embarcacao\n", encoding="utf-8")


def main(destino_local: str = "/content/fase3_dados_locais", drive_celulas: str = DRIVE_CELULAS,
         citra: str = CITRA, celulas: list[str] | None = None, repeat_real: int = REPEAT_REAL) -> dict:
    celulas = celulas or CELULAS
    d = Path(destino_local)

    print("1) Real (train + val) para disco local...")
    rt_img = d / "real" / "train" / "images"; rt_lbl = d / "real" / "train" / "labels"
    rv_img = d / "real" / "val" / "images";   rv_lbl = d / "real" / "val" / "labels"
    print(f"   train: {_copiar_pasta(Path(citra) / 'train/images', rt_img)} img, {_copiar_pasta(Path(citra) / 'train/labels_final', rt_lbl)} lbl | "
          f"val: {_copiar_pasta(Path(citra) / 'val/images', rv_img)} img, {_copiar_pasta(Path(citra) / 'val/labels_final', rv_lbl)} lbl")

    print("\n2) Células (zips) para disco local...")
    contagens = {}
    trainlists = d / "trainlists"; configs = d / "configs"
    trainlists.mkdir(parents=True, exist_ok=True); configs.mkdir(parents=True, exist_ok=True)
    for cel in celulas:
        pasta = d / "celulas" / cel
        pasta.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(Path(drive_celulas) / f"{cel}.zip") as z:
            z.extractall(pasta)
        n_img = len(list((pasta / "images").glob("*.png")))
        c = construir_trainlist_balanceado(rt_img, pasta / "images", trainlists / f"trainlist_{cel}.txt", repeat_real=repeat_real)
        _yaml(configs / f"data_{cel}.yaml", trainlists / f"trainlist_{cel}.txt", rv_img)
        contagens[cel] = c.n_total
        print(f"   {cel}: {n_img} sintéticas | trainlist {c.n_real} real + {c.n_sintetico} sint = {c.n_total} ({c.proporcao_real:.1%} real)")

    print("\n3) Controle (real sobreamostrado, zero sintético)...")
    c = construir_trainlist_real_sobreamostrado(rt_img, trainlists / "trainlist_controle.txt", repeat_real=repeat_real)
    _yaml(configs / "data_controle.yaml", trainlists / "trainlist_controle.txt", rv_img)
    contagens["controle"] = c.n_total
    print(f"   controle: {c.n_real} real = {c.n_total}")

    (configs / "contagens.json").write_text(json.dumps({"repeat_real": repeat_real, "n_imagens_epoca": contagens}, indent=2), encoding="utf-8")
    print(f"\n✅ Preparado em {d}. contagens.json: {contagens}")
    return contagens


if __name__ == "__main__":
    main()

"""
Script de entrada para a Fase 1: prepara todos os dados LOCALMENTE antes
do treino -- extrai as sintéticas de treino e copia as imagens/labels
reais do CITRA (train + val) do Drive para disco local, e monta as três
trainlists (B2, A_joint, controle real-sobreamostrado) + arquivos
data.yaml correspondentes.

Motivo de copiar tudo para local antes de treinar: o treino lê cada
imagem do trainlist uma vez por época -- com centenas de épocas, isso
significa centenas de milhares de leituras. Ler repetidamente do Drive
montado via FUSE é lento e sujeito ao mesmo tipo de instabilidade de I/O
já documentado (ver docs/CHANGELOG_metodologico.md, 2026-09-02, sobre o
OSError do UA-DETRAC) -- só que aqui a leitura repetida durante o treino
seria pior que uma cópia única, não melhor com zip. A solução correta
para treino é copiar tudo para disco local UMA VEZ antes de começar.

Uso no Colab:

    import sys
    sys.path.insert(0, "/content/synth-detection-attribution")
    from scripts.preparar_dados_locais_fase1 import main

    main()
"""
from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

from src.train import construir_trainlist_balanceado, construir_trainlist_real_sobreamostrado

DRIVE_SINTETICAS = "/content/drive/MyDrive/PROJETO_MARINHA/EXPERIMENTO_ATRIBUICAO_CAUSAL/fase1_piloto/sinteticas_treino"
CITRA_TRAIN_IMAGENS_DRIVE = "/content/drive/MyDrive/PROJETO_MARINHA/Datasets/CITRA-3D-Real/train/images"
CITRA_TRAIN_LABELS_DRIVE = "/content/drive/MyDrive/PROJETO_MARINHA/Datasets/CITRA-3D-Real/train/labels_final"
CITRA_VAL_IMAGENS_DRIVE = "/content/drive/MyDrive/PROJETO_MARINHA/Datasets/CITRA-3D-Real/val/images"
CITRA_VAL_LABELS_DRIVE = "/content/drive/MyDrive/PROJETO_MARINHA/Datasets/CITRA-3D-Real/val/labels_final"

REPEAT_REAL = 13  # mesmo fator de variações usado na geração das sintéticas


def _copiar_pasta(origem: Path, destino: Path) -> int:
    destino.mkdir(parents=True, exist_ok=True)
    n = 0
    for caminho in Path(origem).iterdir():
        if caminho.is_file():
            shutil.copy2(caminho, destino / caminho.name)
            n += 1
    return n


def _extrair_zip(caminho_zip: Path, destino: Path) -> None:
    destino.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(caminho_zip) as z:
        z.extractall(destino)


def _escrever_data_yaml(caminho_yaml: Path, train_txt: Path, val_dir: Path) -> None:
    conteudo = (
        f"train: {train_txt}\n"
        f"val: {val_dir}\n"
        f"nc: 1\n"
        f"names:\n"
        f"  - embarcacao\n"
    )
    caminho_yaml.write_text(conteudo, encoding="utf-8")


def main(
    destino_local: str = "/content/fase1_dados_locais",
    drive_sinteticas: str = DRIVE_SINTETICAS,
    citra_train_imagens_drive: str = CITRA_TRAIN_IMAGENS_DRIVE,
    citra_train_labels_drive: str = CITRA_TRAIN_LABELS_DRIVE,
    citra_val_imagens_drive: str = CITRA_VAL_IMAGENS_DRIVE,
    citra_val_labels_drive: str = CITRA_VAL_LABELS_DRIVE,
    repeat_real: int = REPEAT_REAL,
) -> dict:
    destino_local = Path(destino_local)

    print("1) Copiando imagens/labels REAIS do CITRA (train + val) para disco local...")
    real_train_img_local = destino_local / "real" / "train" / "images"
    real_train_lbl_local = destino_local / "real" / "train" / "labels"
    real_val_img_local = destino_local / "real" / "val" / "images"
    real_val_lbl_local = destino_local / "real" / "val" / "labels"

    n1 = _copiar_pasta(citra_train_imagens_drive, real_train_img_local)
    n2 = _copiar_pasta(citra_train_labels_drive, real_train_lbl_local)
    n3 = _copiar_pasta(citra_val_imagens_drive, real_val_img_local)
    n4 = _copiar_pasta(citra_val_labels_drive, real_val_lbl_local)
    print(f"   train: {n1} imagens, {n2} labels | val: {n3} imagens, {n4} labels\n")

    print("2) Extraindo as sintéticas de treino (zips) para disco local...")
    sint_img_local = destino_local / "sinteticas" / "images"
    sint_lbl_local = destino_local / "sinteticas" / "labels"
    _extrair_zip(Path(drive_sinteticas) / "sinteticas_images.zip", sint_img_local)
    _extrair_zip(Path(drive_sinteticas) / "sinteticas_labels.zip", sint_lbl_local)
    n_sint = len(list(sint_img_local.glob("*.png")))
    print(f"   {n_sint} imagens sintéticas extraídas localmente.\n")

    print(f"3) Montando as três trainlists (repeat_real={repeat_real})...")
    trainlists_dir = destino_local / "trainlists"

    contagem_joint = construir_trainlist_balanceado(
        real_train_img_local, sint_img_local, trainlists_dir / "trainlist_A_joint.txt", repeat_real=repeat_real,
    )
    print(f"   A_joint: {contagem_joint.n_real} real + {contagem_joint.n_sintetico} sintético "
          f"= {contagem_joint.n_total} ({contagem_joint.proporcao_real:.1%} real)")

    contagem_controle = construir_trainlist_real_sobreamostrado(
        real_train_img_local, trainlists_dir / "trainlist_controle.txt", repeat_real=repeat_real,
    )
    print(f"   Controle: {contagem_controle.n_real} real, 0 sintético "
          f"= {contagem_controle.n_total} (repetição isolada)")

    # B2 (baseline): sem repetição, sem sintético -- lista simples das imagens reais
    trainlist_b2 = trainlists_dir / "trainlist_B2.txt"
    trainlists_dir.mkdir(parents=True, exist_ok=True)
    imagens_reais = sorted(p for p in real_train_img_local.iterdir() if p.suffix.lower() == ".png")
    trainlist_b2.write_text("\n".join(str(p) for p in imagens_reais) + "\n", encoding="utf-8")
    print(f"   B2 (baseline): {len(imagens_reais)} real, 0 sintético (sem repetição)")

    print("\n4) Gravando data.yaml para cada braço...")
    configs_dir = destino_local / "configs"
    configs_dir.mkdir(parents=True, exist_ok=True)
    for nome_braco, caminho_trainlist in (
        ("B2", trainlist_b2),
        ("A_joint", trainlists_dir / "trainlist_A_joint.txt"),
        ("controle", trainlists_dir / "trainlist_controle.txt"),
    ):
        caminho_yaml = configs_dir / f"data_{nome_braco}.yaml"
        _escrever_data_yaml(caminho_yaml, caminho_trainlist, real_val_img_local)
        print(f"   {caminho_yaml}")

    print(f"\n✅ Dados preparados localmente em {destino_local}")
    print("   Nota: os LABELS das imagens listadas no trainlist devem estar no mesmo "
          "diretório que as imagens correspondentes (convenção Ultralytics: troca "
          "'images' por 'labels' no caminho) -- confirme essa estrutura antes de treinar.")

    return {
        "destino_local": str(destino_local),
        "n_real_train": n1,
        "n_real_val": n3,
        "n_sinteticas": n_sint,
        "contagem_joint": vars(contagem_joint),
        "contagem_controle": vars(contagem_controle),
    }


if __name__ == "__main__":
    main()

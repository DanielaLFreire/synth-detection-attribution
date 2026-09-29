"""
Fase 5, portão G1 -- amostra do conjunto sintético (adendo 3 §4.3). CPU.

1. Extrai o zip de cada célula da Fase 3 do Drive para disco local.
2. Remove as cópias sem colagem (mesma função da Fase 3, commit d82223d)
   e exige 2.592 sintéticas por célula.
3. Sorteia 674 por célula (semente 20260928); M25 = primeiras 337.
4. Grava o manifesto em `configs/amostra_sinteticas_fase5.csv` (no
   repositório) e uma cópia no Drive.

NÃO re-execute depois que o hash do manifesto for registrado: a amostra
vale pelo manifesto commitado, não pela re-execução (que, de todo modo,
reproduz o mesmo resultado -- ver tests/test_amostra_fase5.py).

Uso no Colab:

    import sys
    sys.path.insert(0, "/content/synth-detection-attribution")
    from scripts.amostrar_sinteticas_fase5 import main
    main()

Depois, no repositório:

    python scripts/registrar_artefato.py configs/amostra_sinteticas_fase5.csv
    git add configs/amostra_sinteticas_fase5.csv docs/pre_registro/hashes.json
    git commit -m "fase5: amostra sintética (G1) -- manifesto e hash registrados"
"""
from __future__ import annotations

import hashlib
import shutil
import zipfile
from pathlib import Path

from src.factorial import remover_sinteticas_sem_colagem
from src.factorial.amostra_fase5 import (
    CELULAS_FASE3, amostrar_por_celula, escrever_manifesto, subconjunto_aninhado, achatar,
    N_POR_CELULA_M25,
)

RAIZ_DRIVE = "/content/drive/MyDrive/PROJETO_MARINHA/EXPERIMENTO_ATRIBUICAO_CAUSAL"
DRIVE_CELULAS = f"{RAIZ_DRIVE}/fase3/celulas"
DRIVE_FASE5 = f"{RAIZ_DRIVE}/fase5"
REPO = Path(__file__).resolve().parent.parent
MANIFESTO_REPO = REPO / "configs" / "amostra_sinteticas_fase5.csv"


def extrair_celulas(destino_local: Path, drive_celulas: str = DRIVE_CELULAS) -> dict[str, Path]:
    pastas = {}
    for cel in CELULAS_FASE3:
        pasta = Path(destino_local) / "celulas" / cel
        if not (pasta / "images").exists():
            pasta.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(Path(drive_celulas) / f"{cel}.zip") as z:
                z.extractall(pasta)
        n_rem = remover_sinteticas_sem_colagem(pasta / "images", pasta / "labels", Path(drive_celulas) / f"manifesto_{cel}.csv")
        print(f"   {cel}: removidas {n_rem} cópias sem colagem")
        pastas[cel] = pasta / "images"
    return pastas


def main(destino_local: str = "/content/fase5_dados_locais", drive_celulas: str = DRIVE_CELULAS,
         drive_fase5: str = DRIVE_FASE5, manifesto: Path = MANIFESTO_REPO) -> Path:
    print("1) Células da Fase 3 para disco local...")
    pastas = extrair_celulas(Path(destino_local), drive_celulas)

    print("2) Amostragem estratificada (674/célula, semente 20260928)...")
    amostra = amostrar_por_celula(pastas)
    m25 = subconjunto_aninhado(amostra, N_POR_CELULA_M25)
    print(f"   M50: {len(achatar(amostra))} imagens | M25 (aninhado): {len(achatar(m25))} imagens")

    print("3) Manifesto...")
    n = escrever_manifesto(amostra, manifesto)
    sha = hashlib.sha256(Path(manifesto).read_bytes()).hexdigest()
    Path(drive_fase5).mkdir(parents=True, exist_ok=True)
    shutil.copy2(manifesto, Path(drive_fase5) / Path(manifesto).name)
    print(f"   {n} linhas -> {manifesto}\n   sha256: {sha}")
    print("\nPróximo passo: registrar o hash (scripts/registrar_artefato.py) e commitar ANTES de qualquer treino.")
    return Path(manifesto)


if __name__ == "__main__":
    main()

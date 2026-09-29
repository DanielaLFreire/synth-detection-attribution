"""
Fase 5 -- prepara os dados locais e as 3 trainlists (adendo 3 §4.2). CPU.

Pré-condição: `configs/amostra_sinteticas_fase5.csv` commitado com o hash
registrado em hashes.json (G1). A amostra é LIDA do manifesto, com
conferência de SHA-256 de cada imagem -- nunca re-sorteada aqui.

Trainlists (L = 5.392 em todos os braços):
    C   = real × 4
    M25 = real × 3 + 1.348 sintéticas (subconjunto aninhado)
    M50 = real × 2 + 2.696 sintéticas
Cada trainlist é relida e verificada linha a linha depois de escrita.
As mesmas trainlists servem aos dois orçamentos (S1 e S2 só diferem em épocas).

Uso no Colab (depois de scripts/amostrar_sinteticas_fase5.py ter extraído as células):

    from scripts.preparar_dados_locais_fase5 import main
    main()
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from src.factorial.amostra_fase5 import CELULAS_FASE3, resolver_manifesto
from src.train import construir_trainlist_fracao, verificar_trainlist_fracao
from src.train.passos_fixos import BRACOS, COMPRIMENTO_LISTA, N_REAIS_TREINO, composicao_braco, passos_por_epoca

CITRA = "/content/drive/MyDrive/PROJETO_MARINHA/Datasets/CITRA-3D-Real"
REPO = Path(__file__).resolve().parent.parent
MANIFESTO = REPO / "configs" / "amostra_sinteticas_fase5.csv"


def _copiar(origem: Path, destino: Path) -> int:
    destino.mkdir(parents=True, exist_ok=True)
    n = 0
    for p in Path(origem).iterdir():
        if p.is_file():
            shutil.copy2(p, destino / p.name)
            n += 1
    return n


def main(destino_local: str = "/content/fase5_dados_locais", citra: str = CITRA, manifesto: Path = MANIFESTO) -> dict:
    d = Path(destino_local)
    rt_img, rt_lbl = d / "real/train/images", d / "real/train/labels"
    rv_img, rv_lbl = d / "real/val/images", d / "real/val/labels"
    print("1) Real (train + val) para disco local...")
    print(f"   train {_copiar(Path(citra) / 'train/images', rt_img)} img / {_copiar(Path(citra) / 'train/labels_final', rt_lbl)} lbl; "
          f"val {_copiar(Path(citra) / 'val/images', rv_img)} img / {_copiar(Path(citra) / 'val/labels_final', rv_lbl)} lbl")
    reais = sorted(p for p in rt_img.iterdir() if p.suffix.lower() in (".png", ".jpg", ".jpeg"))
    assert len(reais) == N_REAIS_TREINO, f"{len(reais)} reais de treino, esperado {N_REAIS_TREINO}"

    print("2) Amostra sintética a partir do manifesto (com conferência de SHA-256)...")
    pastas = {cel: d / "celulas" / cel / "images" for cel in CELULAS_FASE3}
    sint = {"C": [], "M25": resolver_manifesto(manifesto, pastas, somente_m25=True),
            "M50": resolver_manifesto(manifesto, pastas)}

    print("3) Trainlists + verificação linha a linha...")
    (d / "configs").mkdir(parents=True, exist_ok=True)
    resumo = {}
    for braco in BRACOS:
        comp = composicao_braco(braco)
        assert len(sint[braco]) == comp.n_sinteticas, f"{braco}: {len(sint[braco])} != {comp.n_sinteticas}"
        txt = d / "trainlists" / f"trainlist_f5_{braco}.txt"
        construir_trainlist_fracao(reais, sint[braco], txt, comp.repeat_real)
        c = verificar_trainlist_fracao(txt, reais, sint[braco], comp.repeat_real, COMPRIMENTO_LISTA)
        (d / "configs" / f"data_f5_{braco}.yaml").write_text(
            f"train: {txt}\nval: {rv_img}\nnc: 1\nnames:\n  - embarcacao\n", encoding="utf-8")
        resumo[braco] = {"n_total": c.n_total, "n_real": c.n_real, "n_sintetico": c.n_sintetico,
                         "fracao_sintetica": c.n_sintetico / c.n_total, "passos_por_epoca": passos_por_epoca(c.n_total)}
        print(f"   {braco}: {c.n_real} real + {c.n_sintetico} sint = {c.n_total} "
              f"(p = {c.n_sintetico / c.n_total:.4f}, {passos_por_epoca(c.n_total)} passos/época)")
    (d / "configs" / "contagens_f5.json").write_text(json.dumps(resumo, indent=2), encoding="utf-8")
    print(f"\n✅ Preparado em {d}")
    return resumo


if __name__ == "__main__":
    main()

"""
Fase 4 -- avaliação ÚNICA no split de TESTE do CITRA-3D-Real (§7 do plano).

Lista de modelos FIXADA antes de rodar (não é selecionável):
- 15 da Fase 3: {casada__alto, casada__baixo, reduzida__alto, reduzida__baixo,
  controle} × seeds {42, 123, 2024} -- `weights/last.pt` (época 150).
- 3 de referência da Fase 1: B2 × seeds -- `weights/last.pt`.

Métricas por modelo:
- Primária: recall / mAP50 / mAP50-95 no ponto de máximo-F1 (mesma
  definição do results.csv de treino), via `model.val`.
- F2: recall por tamanho (small < 32 px a 640 vs não-small) a conf >= 0,25,
  IoU >= 0,5, casamento guloso (definição da Fase 3).

Contrastes pré-registrados (adendo 2 §5) recalculados sobre o teste.

TRAVA: grava `fase4/teste_avaliado.json` no Drive; uma segunda chamada é
recusada. GPU ou CPU (18 modelos × ~N imagens de teste -- leve).

Uso no Colab:

    import sys
    sys.path.insert(0, "/content/synth-detection-attribution")
    from scripts.avaliar_teste_fase4 import main
    main()
"""
from __future__ import annotations

import csv
import json
import shutil
import subprocess
from pathlib import Path

from src.evaluation import verificar_avaliacao_unica, registrar_avaliacao
from src.factorial import analisar_fatorial
from scripts.recall_por_tamanho_fase3 import _gts, _recall_por_estrato

RAIZ = "/content/drive/MyDrive/PROJETO_MARINHA/EXPERIMENTO_ATRIBUICAO_CAUSAL"
CITRA = "/content/drive/MyDrive/PROJETO_MARINHA/Datasets/CITRA-3D-Real"
RUNS_FASE3 = f"{RAIZ}/fase3/runs"
RUNS_FASE1 = f"{RAIZ}/fase1_piloto/runs"
DESTINO = f"{RAIZ}/fase4"
MARCADOR = f"{DESTINO}/teste_avaliado.json"
SEEDS = [42, 123, 2024]
BRACOS_FASE3 = ["casada__alto", "casada__baixo", "reduzida__alto", "reduzida__baixo", "controle"]


def _modelos() -> list[tuple[str, str, int, Path]]:
    """(grupo, braço, seed, caminho) -- lista fixa."""
    lista = [("fase3", b, s, Path(RUNS_FASE3) / f"{b}_seed{s}" / "weights" / "last.pt") for s in SEEDS for b in BRACOS_FASE3]
    lista += [("fase1_ref", "B2", s, Path(RUNS_FASE1) / f"B2_seed{s}" / "weights" / "last.pt") for s in SEEDS]
    return lista


def _commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "desconhecido"


def _preparar_teste_local(citra: Path, local: Path) -> tuple[Path, Path, Path]:
    """Copia test/images e test/labels_final para local/test/{images,labels}
    (Ultralytics procura labels/ ao lado de images/). Retorna (yaml, images, labels)."""
    img = local / "test" / "images"; lbl = local / "test" / "labels"
    img.mkdir(parents=True, exist_ok=True); lbl.mkdir(parents=True, exist_ok=True)
    for p in (citra / "test" / "images").iterdir():
        if p.is_file(): shutil.copy2(p, img / p.name)
    for p in (citra / "test" / "labels_final").iterdir():
        if p.is_file(): shutil.copy2(p, lbl / p.name)
    yaml = local / "data_teste.yaml"
    yaml.write_text(f"train: {img}\nval: {img}\nnc: 1\nnames:\n  - embarcacao\n", encoding="utf-8")
    return yaml, img, lbl


def main(citra: str = CITRA, destino: str = DESTINO, local: str = "/content/fase4_local") -> dict:
    from ultralytics import YOLO

    verificar_avaliacao_unica(Path(MARCADOR))  # trava -- recusa se já avaliado

    modelos = _modelos()
    faltando = [str(p) for *_, p in modelos if not p.exists()]
    if faltando:
        raise FileNotFoundError(f"Modelos ausentes no Drive (nada avaliado): {faltando}")

    print("1) Split de teste para disco local...")
    yaml, img, lbl = _preparar_teste_local(Path(citra), Path(local))
    gts = _gts(img, lbl)
    n_small = sum(s for cs in gts.values() for _, s in cs); n_tot = sum(len(cs) for cs in gts.values())
    print(f"   teste: {len(gts)} imagens, {n_tot} caixas, {n_small} small ({100*n_small/max(n_tot,1):.1f}%)\n")

    print("2) Avaliando os 18 modelos (lista fixa)...")
    linhas = []
    for grupo, braco, seed, pesos in modelos:
        m = YOLO(str(pesos))
        v = m.val(data=str(yaml), imgsz=640, verbose=False, plots=False)
        f2 = _recall_por_estrato(m, img, gts)
        linha = {"grupo": grupo, "braco": braco, "seed": seed,
                 "recall": float(v.box.mr), "precisao": float(v.box.mp), "mAP50": float(v.box.map50), "mAP50_95": float(v.box.map),
                 "recall_small_conf025": f2["small"], "recall_nao_small_conf025": f2["nao_small"]}
        linhas.append(linha)
        print(f"   {grupo:<10} {braco:<16} seed {seed:<5} recall={linha['recall']:.4f} mAP50={linha['mAP50']:.4f} | small={f2['small']:.4f} nao_small={f2['nao_small']:.4f}")

    Path(destino).mkdir(parents=True, exist_ok=True)
    with open(Path(destino) / "teste_metricas.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0].keys())); w.writeheader(); w.writerows(linhas)

    print("\n3) Contrastes pré-registrados sobre o TESTE (recall primário)...")
    rec = {b: {s: next(l["recall"] for l in linhas if l["grupo"] == "fase3" and l["braco"] == b and l["seed"] == s) for s in SEEDS} for b in BRACOS_FASE3}
    out = analisar_fatorial(rec)
    def mostra(c):
        print(f"   {c.nome:<36} {c.media_pp:+.2f} pp  [{', '.join(f'{v:+.2f}' for v in c.por_seed_pp.values())}]  d={c.d_cohen:+.2f}  -> {c.veredito.upper()}")
    mostra(out["F1"]["P5b"]); mostra(out["F1"]["P8"]); mostra(out["F3"]["P9"])
    for _, c in out["F3"]["P10_por_celula"].items(): mostra(c)
    mostra(out["F3"]["P10_media"])

    def ser(c): return dict(c.__dict__)
    resumo = {
        "n_imagens_teste": len(gts), "n_caixas_teste": n_tot, "n_small": n_small,
        "recall_teste": rec, "anova": out["anova_2x2_bloco_seed"].__dict__,
        "F1": {k: ser(v) for k, v in out["F1"].items()},
        "F3": {"P9": ser(out["F3"]["P9"]), "P10_media": ser(out["F3"]["P10_media"]),
               "P10_por_celula": {b: ser(c) for b, c in out["F3"]["P10_por_celula"].items()}},
        "B2_referencia": {l["seed"]: l["recall"] for l in linhas if l["grupo"] == "fase1_ref"},
    }
    (Path(destino) / "teste_analise.json").write_text(json.dumps(resumo, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    registro = registrar_avaliacao(Path(MARCADOR), {"commit": _commit(), "n_modelos": len(modelos),
                                                    "modelos": [f"{g}/{b}_seed{s}" for g, b, s, _ in modelos],
                                                    "n_imagens_teste": len(gts), "n_caixas_teste": n_tot})
    print(f"\n✅ Teste avaliado UMA vez. Marcador gravado: {MARCADOR}")
    return resumo


if __name__ == "__main__":
    main()

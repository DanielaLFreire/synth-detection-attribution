"""
Fase 5 -- avaliação ÚNICA no split de TESTE (adendo 3 §9).

Segunda avaliação do teste no projeto (a primeira foi a Fase 4), legítima
só porque foi pré-registrada no adendo 3 com lista fixa: os 30 `last.pt`
de §4.5, os mesmos do manifesto `fase5/modelos_fase5.json`, gravado pela
análise de validação. A execução de portão (G2rep) fica de fora.

`verificar()` (CPU, sem carregar modelos) exige GO em todas as checagens:
 1. análise de validação já executada (as decisões saem do val, §9);
 2. marcador `fase5/teste_avaliado.json` ausente;
 3. os 30 `last.pt` existem e o SHA-256 de cada um bate com o manifesto;
 4. teste: imagens e labels pareados;
 5. isolamento por NOME contra train e val;
 6. isolamento por CONTEÚDO (md5) contra train e val;
 7. isolamento contra a amostra sintética da Fase 5 (imagens-base do
    manifesto `configs/amostra_sinteticas_fase5.csv`).

`main()` roda `verificar()`, avalia os 30 modelos (recall no ponto de
máximo-F1 e mAP50 via model.val, como na Fase 4; estrato small com a
definição da Fase 3), calcula F1 e F2 (F2c não é calculável no teste; ver
`F2C_NAO_APLICAVEL`), compara com a validação (§9: réplica = mesma
categoria) e grava o marcador por último.

Uso no Colab (GPU):

    import sys
    sys.path.insert(0, "/content/synth-detection-attribution")
    from scripts.avaliar_teste_fase5 import verificar, main
    verificar()     # só checagens; nada é avaliado
    main()          # avaliação única
"""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path

from src.evaluation import (hashes_imagens, pareamento_imagens_labels, registrar_avaliacao, stems_imagens,
                            verificar_avaliacao_unica, verificar_disjuncao)
from src.factorial.amostra_fase5 import ler_manifesto
from src.factorial.analise_fase5 import BRACOS, ORCAMENTOS, SEEDS, analisar_teste, comparar_replicacao, tabela_markdown
from src.train.passos_fixos import planejar_execucoes

RAIZ = "/content/drive/MyDrive/PROJETO_MARINHA/EXPERIMENTO_ATRIBUICAO_CAUSAL"
CITRA = "/content/drive/MyDrive/PROJETO_MARINHA/Datasets/CITRA-3D-Real"
FASE5 = f"{RAIZ}/fase5"
REPO = Path(__file__).resolve().parent.parent


class TesteNaoLiberado(RuntimeError):
    pass


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def _commit() -> str:
    try:
        return subprocess.check_output(["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "desconhecido"


def imagens_base_da_amostra(manifesto_csv: Path) -> set[str]:
    """Stems das imagens-base (reais de treino) usadas nas sintéticas da Fase 5."""
    with open(manifesto_csv, newline="", encoding="utf-8") as f:
        return {linha["imagem_base"] for linha in csv.DictReader(f)}


def verificar(fase5: str = FASE5, citra: str = CITRA,
              manifesto_amostra: Path = REPO / "configs" / "amostra_sinteticas_fase5.csv") -> list[str]:
    """Devolve a lista de problemas (vazia = GO). Não carrega modelos."""
    fase5_p, citra_p = Path(fase5), Path(citra)
    problemas: list[str] = []

    def chk(cond: bool, msg: str) -> None:
        print(f"  {'✅' if cond else '❌'} {msg}")
        if not cond:
            problemas.append(msg)

    print("1) Pré-condições")
    chk((fase5_p / "analise_val_executada.json").exists(), "análise de validação já executada")
    chk(not (fase5_p / "teste_avaliado.json").exists(), "marcador fase5/teste_avaliado.json ausente")

    print("2) Modelos: lista fixa e SHA-256 contra o manifesto da validação")
    man_path = fase5_p / "modelos_fase5.json"
    if not man_path.exists():
        chk(False, "manifesto modelos_fase5.json presente")
    else:
        manifesto = json.loads(man_path.read_text(encoding="utf-8"))
        plano = [e.nome for e in planejar_execucoes()]
        chk(sorted(manifesto) == sorted(plano), f"manifesto = lista fechada de {len(plano)} execuções")
        divergentes = [n for n in plano if not (fase5_p / "runs" / n / "weights" / "last.pt").exists()
                       or _sha256(fase5_p / "runs" / n / "weights" / "last.pt") != manifesto.get(n)]
        chk(not divergentes, f"SHA-256 dos last.pt = manifesto ({len(plano) - len(divergentes)}/{len(plano)})"
            + (f"  divergentes: {divergentes[:3]}" if divergentes else ""))

    print("3) Split de teste: estrutura e isolamento")
    t_img, t_lbl = citra_p / "test" / "images", citra_p / "test" / "labels_final"
    if not (t_img.is_dir() and t_lbl.is_dir()):
        chk(False, f"pastas do teste em {citra_p / 'test'}")
        return problemas
    par = pareamento_imagens_labels(t_img, t_lbl)
    chk(not par["imagens_sem_label"] and not par["labels_sem_imagem"],
        f"{par['n_imagens']} imagens / {par['n_labels']} labels pareados")
    s_test = stems_imagens(t_img)
    for nome, v in verificar_disjuncao(s_test, {"train": stems_imagens(citra_p / "train" / "images"),
                                                  "val": stems_imagens(citra_p / "val" / "images")}).items():
        chk(not v, f"nome: teste ∩ {nome} = {len(v)}")
    h_test = hashes_imagens(t_img)
    for nome in ("train", "val"):
        comuns = set(h_test) & set(hashes_imagens(citra_p / nome / "images"))
        chk(not comuns, f"conteúdo (md5): teste ∩ {nome} = {len(comuns)}")
    base = imagens_base_da_amostra(Path(manifesto_amostra))
    v = sorted(s_test & base)
    chk(not v, f"teste ∩ imagens-base da amostra sintética da Fase 5 = {len(v)}")

    print("\n" + ("✅ GO" if not problemas else f"❌ NO-GO: {len(problemas)} problema(s)"))
    return problemas


def main(fase5: str = FASE5, citra: str = CITRA, local: str = "/content/fase5_teste_local") -> dict:
    from ultralytics import YOLO
    from scripts.avaliar_teste_fase4 import _preparar_teste_local
    from scripts.recall_por_tamanho_fase3 import _gts, _recall_por_estrato

    marcador = Path(fase5) / "teste_avaliado.json"
    verificar_avaliacao_unica(marcador)
    problemas = verificar(fase5, citra)
    if problemas:
        raise TesteNaoLiberado(f"verificar() com {len(problemas)} problema(s); nada foi avaliado.")

    print("\n4) Teste para disco local...")
    yaml, img, lbl = _preparar_teste_local(Path(citra), Path(local))
    gts = _gts(img, lbl)
    n_tot = sum(len(cs) for cs in gts.values())
    n_small = sum(s for cs in gts.values() for _, s in cs)
    print(f"   {len(gts)} imagens, {n_tot} caixas, {n_small} small")

    print("5) Avaliando os 30 modelos (lista fixa)...")
    vazio = lambda: {o: {b: {} for b in BRACOS} for o in ORCAMENTOS}  # noqa: E731
    recall, map50, small, linhas = vazio(), vazio(), vazio(), []
    for e in planejar_execucoes():
        m = YOLO(str(Path(fase5) / "runs" / e.nome / "weights" / "last.pt"))
        v = m.val(data=str(yaml), imgsz=640, verbose=False, plots=False)
        f2 = _recall_por_estrato(m, img, gts)
        recall[e.orcamento][e.braco][e.seed] = float(v.box.mr)
        map50[e.orcamento][e.braco][e.seed] = float(v.box.map50)
        small[e.orcamento][e.braco][e.seed] = f2["small"]
        linhas.append({"execucao": e.nome, "orcamento": e.orcamento, "braco": e.braco, "seed": e.seed,
                       "recall": float(v.box.mr), "precisao": float(v.box.mp), "mAP50": float(v.box.map50),
                       "mAP50_95": float(v.box.map), "recall_small": f2["small"], "recall_nao_small": f2["nao_small"]})
        print(f"   {e.nome}: ok")

    destino = Path(fase5)
    with open(destino / "teste_metricas_fase5.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)

    print("6) Análise pré-registrada sobre o teste e comparação com a validação...")
    resultado = analisar_teste(recall, map50, small)
    val = json.loads((destino / "resultados_val_fase5.json").read_text(encoding="utf-8"))
    resultado["replicacao"] = comparar_replicacao(val, resultado)
    resultado.update({"n_imagens_teste": len(gts), "n_caixas_teste": n_tot, "n_small": n_small, "commit": _commit()})
    (destino / "resultados_teste_fase5.json").write_text(json.dumps(resultado, indent=2, ensure_ascii=False), encoding="utf-8")

    registrar_avaliacao(marcador, {
        "commit": resultado["commit"], "n_modelos": len(linhas),
        "modelos_sha256": json.loads((destino / "modelos_fase5.json").read_text(encoding="utf-8")),
        "n_imagens_teste": len(gts), "n_caixas_teste": n_tot,
        "sha256_resultados": _sha256(destino / "resultados_teste_fase5.json"),
    })

    print(tabela_markdown(resultado, familias=("F1", "F2")))
    print(f"\nF2c: {resultado['F2c']}")
    print("\nRéplica (§9: mesma categoria de §6.1):")
    for r in resultado["replicacao"]:
        print(f"   {r['contraste']}: val {r['veredito_val']} ({r['media_val_pp']:+.2f}) | "
              f"teste {r['veredito_teste']} ({r['media_teste_pp']:+.2f}) -> {'REPLICA' if r['replica'] else 'não replica'}")
    a = resultado["anova_2x3_bloco_seed"]
    print("\nANOVA 2×3 (teste): " + "; ".join(f"{k} F = {a['f'][k]:.2f}, p = {a['p'][k]:.3f}" for k in a["f"]))
    print(f"\n✅ Teste avaliado UMA vez. Marcador: {marcador}")
    return resultado


if __name__ == "__main__":
    main()

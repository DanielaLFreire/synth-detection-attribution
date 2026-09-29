"""
Fase 5 -- análise no split de VALIDAÇÃO (adendo 3 §5–§7). Execução ÚNICA.

Pré-condições, verificadas antes de ler qualquer métrica:
- G2 com veredito GO;
- as 30 execuções da lista fechada concluídas (G3 incluído);
- nenhuma análise anterior registrada (trava `analise_val_executada.json`).

Passos:
1. Manifesto dos modelos: SHA-256 COMPLETO de cada `last.pt`
   (`fase5/modelos_fase5.json`), que servirá também à trava do teste.
2. Métricas do results.csv (recall e mAP50 da última época, área sob a
   curva, pico).
3. Estrato small (F2a) com inferência de cada `last.pt` no val (GPU,
   ~1 min por modelo), com a mesma definição da Fase 3.
4. Análise (src/factorial/analise_fase5.py) -> `fase5/resultados_val_fase5.json`
   e `.md`; a trava é gravada SÓ depois de os resultados estarem salvos.

Uso no Colab (GPU), depois da sequência de início de sessão:

    import sys
    sys.path.insert(0, "/content/synth-detection-attribution")
    from scripts.analisar_fase5 import main
    main()
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from src.factorial.analise_fase5 import BRACOS, ORCAMENTOS, SEEDS, analisar, metricas_de_results, tabela_markdown
from src.train.passos_fixos import ORCAMENTOS as ORC_DESENHO, planejar_execucoes

RAIZ = "/content/drive/MyDrive/PROJETO_MARINHA/EXPERIMENTO_ATRIBUICAO_CAUSAL/fase5"
VAL_IMAGES = "/content/drive/MyDrive/PROJETO_MARINHA/Datasets/CITRA-3D-Real/val/images"
VAL_LABELS = "/content/drive/MyDrive/PROJETO_MARINHA/Datasets/CITRA-3D-Real/val/labels_final"


class AnaliseJaExecutada(RuntimeError):
    pass


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def verificar_pronto(raiz: str = RAIZ) -> None:
    from scripts.treinar_fase5 import estado, portao_aprovado
    raiz_p = Path(raiz)
    if (raiz_p / "analise_val_executada.json").exists():
        raise AnaliseJaExecutada("A análise de validação da Fase 5 já foi executada (execução única).")
    if not portao_aprovado(str(raiz_p / "portao_g2.json")):
        raise RuntimeError("G2 sem veredito GO.")
    pend = [e.nome for e in planejar_execucoes() if estado(e, str(raiz_p / "runs")) != "concluida"]
    if pend:
        raise RuntimeError(f"{len(pend)} execução(ões) não concluída(s): {pend}")


def main(raiz: str = RAIZ, val_images: str = VAL_IMAGES, val_labels: str = VAL_LABELS,
         calcular_small: bool = True) -> dict:
    verificar_pronto(raiz)
    runs = Path(raiz) / "runs"
    plano = planejar_execucoes()

    print("1) Manifesto dos modelos (SHA-256 completo de cada last.pt)...")
    manifesto = {e.nome: _sha256(runs / e.nome / "weights" / "last.pt") for e in plano}
    if len(set(manifesto.values())) != len(manifesto):
        raise RuntimeError("Há last.pt idênticos entre execuções diferentes.")
    (Path(raiz) / "modelos_fase5.json").write_text(json.dumps(manifesto, indent=2), encoding="utf-8")

    print("2) Métricas do results.csv...")
    vazio = lambda: {o: {b: {} for b in BRACOS} for o in ORCAMENTOS}  # noqa: E731
    recall, map50, auc, small, pico, por_execucao = vazio(), vazio(), vazio(), vazio(), vazio(), {}
    for e in plano:
        m = metricas_de_results(runs / e.nome / "results.csv", ORC_DESENHO[e.orcamento].epocas)
        recall[e.orcamento][e.braco][e.seed] = m.recall
        map50[e.orcamento][e.braco][e.seed] = m.map50
        auc[e.orcamento][e.braco][e.seed] = m.auc
        pico[e.orcamento][e.braco][e.seed] = m.passo_pico
        por_execucao[e.nome] = asdict(m)

    print("3) Estrato small (F2a), inferência no val...")
    if calcular_small:
        from ultralytics import YOLO
        from scripts.recall_por_tamanho_fase3 import _gts, _recall_por_estrato
        gts = _gts(Path(val_images), Path(val_labels))
        for e in plano:
            r = _recall_por_estrato(YOLO(str(runs / e.nome / "weights" / "last.pt")), Path(val_images), gts)
            small[e.orcamento][e.braco][e.seed] = r["small"]
            por_execucao[e.nome]["small"] = r["small"]
            por_execucao[e.nome]["nao_small"] = r["nao_small"]
            print(f"   {e.nome}: ok")
    else:
        raise RuntimeError("calcular_small=False só é permitido em teste; F2a é pré-registrada.")

    print("4) Análise pré-registrada...")
    resultado = analisar(recall, map50, auc, small, pico)
    resultado["por_execucao"] = por_execucao
    resultado["manifesto_modelos_sha256"] = manifesto
    resultado["gerado_em_utc"] = datetime.now(timezone.utc).isoformat()

    destino = Path(raiz)
    (destino / "resultados_val_fase5.json").write_text(json.dumps(resultado, indent=2, ensure_ascii=False), encoding="utf-8")
    md = tabela_markdown(resultado)
    (destino / "resultados_val_fase5.md").write_text(md, encoding="utf-8")
    (destino / "analise_val_executada.json").write_text(json.dumps({
        "executada_em_utc": resultado["gerado_em_utc"],
        "sha256_resultados": _sha256(destino / "resultados_val_fase5.json"),
    }, indent=2), encoding="utf-8")

    print(md)
    a = resultado["anova_2x3_bloco_seed"]
    print("\nANOVA 2×3 (seed como bloco): " + "; ".join(
        f"{k} F({a['df'][k]},{a['df']['erro']}) = {a['f'][k]:.2f}, p = {a['p'][k]:.3f}" for k in a["f"]))
    print(f"\nSalvo em {destino}/resultados_val_fase5.json (trava gravada).")
    return resultado


if __name__ == "__main__":
    main()

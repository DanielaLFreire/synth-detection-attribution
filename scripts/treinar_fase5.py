"""
Fase 5 -- treino com passos igualados (adendo 3, commit 3004384). GPU.

Ordem obrigatória:
    1. `portao_g2()`  -- f5_S1_C_seed42 duas vezes; compara; grava o
       veredito (GO/NO-GO) UMA vez em `fase5/portao_g2.json` no Drive.
    2. `main()`       -- as 30 execuções da lista fechada (§4.5). Recusa
       rodar sem o veredito GO do G2.

Execução retomável: `main()` roda só o que falta, em ordem fixa (orçamento,
seed, braço), e pode ser chamada em várias sessões. Uma execução é
"concluída" (G3) se tem o nº de épocas do orçamento, last.pt E contagem
REAL de iterações igual a épocas × 337 (`passos_f5.json`, gravado por
callback).

- Execução INCOMPLETA (desconexão): é refeita do zero com a mesma seed.
- Execução COMPLETA com passos errados: violação de protocolo. O script
  PARA; não se re-roda até achar a causa (registro em novo adendo).

Uso no Colab (GPU), depois de preparar_dados_locais_fase5.main():

    import sys
    sys.path.insert(0, "/content/synth-detection-attribution")
    from scripts.treinar_fase5 import listar, portao_g2, main

    portao_g2()              # G2; ~0,8 h
    listar()                 # estado
    main(max_execucoes=6)    # ou main() para rodar tudo o que falta
"""
from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from src.train import copiar_resultados_para_drive, execucao_concluida
from src.train.passos_fixos import ORCAMENTOS, ExecucaoF5, execucoes_portao_g2, kwargs_execucao, planejar_execucoes
from src.train.verificacao_fase5 import (
    _ambiente, NOME_JSON_PASSOS, ContadorPassos, comparar_pesos, verificar_passos, verificar_pre_requisitos, veredito_g2,
)

REPO = Path(__file__).resolve().parent.parent
RAIZ_DRIVE = "/content/drive/MyDrive/PROJETO_MARINHA/EXPERIMENTO_ATRIBUICAO_CAUSAL/fase5"
DADOS_LOCAIS = "/content/fase5_dados_locais"
DESTINO_RUNS = "/content/fase5_runs"
DESTINO_RUNS_DRIVE = f"{RAIZ_DRIVE}/runs"
ARQUIVO_G2 = f"{RAIZ_DRIVE}/portao_g2.json"


class ViolacaoDeProtocolo(RuntimeError):
    pass


class PortaoNaoAprovado(RuntimeError):
    pass


class AmbienteDivergente(RuntimeError):
    pass


CHAVES_AMBIENTE = ("gpu", "torch", "ultralytics")


def diferencas_ambiente(registrado: dict, atual: dict) -> dict:
    """Chaves de ambiente (GPU, torch, ultralytics) que mudaram desde o G2."""
    return {k: (registrado.get(k), atual.get(k)) for k in CHAVES_AMBIENTE if registrado.get(k) != atual.get(k)}


def estado(execucao: ExecucaoF5, destino_runs_drive: str = DESTINO_RUNS_DRIVE) -> str:
    """'concluida' | 'pendente' | 'violacao' (completa, mas passos errados)."""
    pasta = Path(destino_runs_drive) / execucao.nome
    if not execucao_concluida(pasta, ORCAMENTOS[execucao.orcamento].epocas):
        return "pendente"
    return "violacao" if verificar_passos(pasta / NOME_JSON_PASSOS, execucao.orcamento) else "concluida"


def listar(destino_runs_drive: str = DESTINO_RUNS_DRIVE, arquivo_g2: str = ARQUIVO_G2) -> list[ExecucaoF5]:
    g2 = Path(arquivo_g2)
    print(f"Portão G2: {json.loads(g2.read_text())['veredito'] if g2.exists() else 'não executado'}")
    plano = planejar_execucoes()
    estados = {e: estado(e, destino_runs_drive) for e in plano}
    pend = [e for e in plano if estados[e] != "concluida"]
    print(f"Planejadas: {len(plano)} | concluídas: {len(plano) - len(pend)} | pendentes: {len(pend)}")
    icones = {"concluida": "✅", "pendente": "⏳", "violacao": "❌"}
    for e in plano:
        print(f"  {icones[estados[e]]} {e.nome}")
    return pend


def treinar(execucao: ExecucaoF5, dados_locais: str = DADOS_LOCAIS, destino_runs: str = DESTINO_RUNS,
            destino_runs_drive: str = DESTINO_RUNS_DRIVE) -> None:
    from ultralytics import YOLO  # import tardio -- GPU

    data_yaml = Path(dados_locais) / "configs" / f"data_f5_{execucao.braco}.yaml"
    if not data_yaml.exists():
        raise FileNotFoundError(data_yaml)
    kwargs = kwargs_execucao(execucao)
    model_path = kwargs.pop("model")
    kwargs.pop("_epoca_checkpoint_a_usar")

    local = Path(destino_runs) / execucao.nome
    if local.exists():
        # o Ultralytics ACRESCENTA linhas a um results.csv existente; uma
        # execução refeita precisa começar de pasta vazia
        shutil.rmtree(local)

    model = YOLO(model_path)
    ContadorPassos(local / NOME_JSON_PASSOS).registrar(model)
    model.train(data=str(data_yaml), project=str(destino_runs), deterministic=True, exist_ok=True, **kwargs)
    copiar_resultados_para_drive(local, Path(destino_runs_drive) / execucao.nome)

    situacao = estado(execucao, destino_runs_drive)
    if situacao != "concluida":
        problemas = verificar_passos(Path(destino_runs_drive) / execucao.nome / NOME_JSON_PASSOS, execucao.orcamento)
        raise ViolacaoDeProtocolo(f"{execucao.nome} terminou em estado '{situacao}': {problemas}")


def _exigir_pre_requisitos(dados_locais: str) -> None:
    problemas = verificar_pre_requisitos(REPO, Path(dados_locais))
    if problemas:
        raise RuntimeError("Pré-requisitos não atendidos: " + "; ".join(problemas))


def portao_g2(dados_locais: str = DADOS_LOCAIS, destino_runs: str = DESTINO_RUNS,
              destino_runs_drive: str = DESTINO_RUNS_DRIVE, arquivo_g2: str = ARQUIVO_G2) -> dict:
    """Executa (ou retoma) as duas execuções do G2 e grava o veredito UMA vez."""
    g2 = Path(arquivo_g2)
    if g2.exists():
        registro = json.loads(g2.read_text(encoding="utf-8"))
        print(f"G2 já registrado ({registro['registrado_em_utc']}): {registro['veredito']}. Não é re-executado.")
        return registro

    _exigir_pre_requisitos(dados_locais)
    original, repeticao = execucoes_portao_g2()
    for e in (original, repeticao):
        s = estado(e, destino_runs_drive)
        if s == "violacao":
            raise ViolacaoDeProtocolo(f"{e.nome} está completa com passos errados")
        if s == "pendente":
            print(f"\n=== G2: treinando {e.nome} ===")
            treinar(e, dados_locais, destino_runs, destino_runs_drive)

    pa, pb = Path(destino_runs_drive) / original.nome, Path(destino_runs_drive) / repeticao.nome
    registro = veredito_g2(pa / "results.csv", pb / "results.csv", pa / NOME_JSON_PASSOS, pb / NOME_JSON_PASSOS)
    try:
        registro["pesos_adicional_informativo"] = comparar_pesos(pa / "weights" / "last.pt", pb / "weights" / "last.pt")
    except Exception as exc:  # informativo: falha aqui não altera o veredito
        registro["pesos_adicional_informativo"] = {"erro": repr(exc)}
    registro["execucoes"] = [original.nome, repeticao.nome]
    registro["ambiente"] = json.loads((pa / NOME_JSON_PASSOS).read_text(encoding="utf-8")).get("ambiente", {})
    registro["registrado_em_utc"] = datetime.now(timezone.utc).isoformat()
    g2.parent.mkdir(parents=True, exist_ok=True)
    g2.write_text(json.dumps(registro, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nG2: {registro['veredito']}")
    print(f"  results.csv idêntico (exceto time): {registro['results_identico']} {registro['motivo']}")
    print(f"  G3 execução 1: {registro['g3_execucao_1'] or 'ok'} | execução 2: {registro['g3_execucao_2'] or 'ok'}")
    print(f"  pesos (informativo): {registro['pesos_adicional_informativo']}")
    print(f"  registrado em {g2}")
    return registro


def portao_aprovado(arquivo_g2: str = ARQUIVO_G2) -> bool:
    g2 = Path(arquivo_g2)
    return g2.exists() and json.loads(g2.read_text(encoding="utf-8")).get("veredito") == "GO"


def main(max_execucoes: int | None = None, dados_locais: str = DADOS_LOCAIS, destino_runs: str = DESTINO_RUNS,
         destino_runs_drive: str = DESTINO_RUNS_DRIVE, arquivo_g2: str = ARQUIVO_G2,
         permitir_ambiente_diferente: bool = False) -> list[str]:
    if not portao_aprovado(arquivo_g2):
        raise PortaoNaoAprovado("O G2 não tem veredito GO registrado; rode portao_g2() primeiro (adendo 3 §8).")
    # O determinismo do G2 só vale no mesmo hardware e nas mesmas versões.
    # Mudar de GPU/versão no meio da campanha exige decisão explícita
    # (permitir_ambiente_diferente=True) E registro no changelog.
    difs = diferencas_ambiente(json.loads(Path(arquivo_g2).read_text(encoding="utf-8")).get("ambiente", {}), _ambiente())
    if difs and not permitir_ambiente_diferente:
        raise AmbienteDivergente(f"Ambiente difere do G2 (registrado, atual): {difs}")
    if difs:
        print(f"⚠️  Ambiente difere do G2 (registrado, atual): {difs} -- registrar no changelog.")
    _exigir_pre_requisitos(dados_locais)
    pend = listar(destino_runs_drive, arquivo_g2)
    violacoes = [e.nome for e in pend if estado(e, destino_runs_drive) == "violacao"]
    if violacoes:
        raise ViolacaoDeProtocolo(f"Execuções completas com passos errados: {violacoes}")
    if max_execucoes is not None:
        pend = pend[:max_execucoes]
    feitas = []
    for e in pend:
        print(f"\n=== Treinando {e.nome} ({ORCAMENTOS[e.orcamento].passos_totais} passos) ===")
        treinar(e, dados_locais, destino_runs, destino_runs_drive)
        feitas.append(e.nome)
    print(f"\nConcluídas nesta sessão: {feitas}")
    listar(destino_runs_drive, arquivo_g2)
    return feitas


if __name__ == "__main__":
    main()

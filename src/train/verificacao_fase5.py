"""
Fase 5 -- portões G2 (determinismo) e G3 (integridade) do adendo 3 §8.

- G2: `f5_S1_C_seed42` executado duas vezes; critério LACRADO: métricas
  idênticas em todas as colunas do results.csv, exceto tempo. A comparação
  de pesos (tensores do last.pt) é reportada como verificação ADICIONAL,
  informativa: não entra no veredito, que segue a letra do adendo.
- G3: cada execução precisa ter o número de épocas do orçamento, last.pt e
  número de iterações REAIS igual a épocas × 337. As iterações são
  contadas por callback do Ultralytics (um incremento por lote), e não
  deduzidas da configuração. O callback também grava o tamanho do dataset
  que o treinador de fato montou; isso prova que as linhas repetidas da
  trainlist não foram deduplicadas.

Nada aqui importa ultralytics nem torch no nível do módulo: os testes
rodam em CPU sem essas dependências.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from dataclasses import dataclass, field
from pathlib import Path

from .passos_fixos import COMPRIMENTO_LISTA, ORCAMENTOS, passos_por_epoca

NOME_JSON_PASSOS = "passos_f5.json"
COLUNAS_IGNORADAS_G2 = ("time",)


# ---------------------------------------------------------------------------
# G2 -- comparação de results.csv
# ---------------------------------------------------------------------------

@dataclass
class ComparacaoResultados:
    identico: bool
    n_linhas: tuple[int, int]
    colunas_comparadas: list[str]
    divergencias: dict[str, dict] = field(default_factory=dict)  # coluna -> {primeira_epoca, max_abs_diff}
    motivo: str = ""


def _ler_results(caminho: Path) -> tuple[list[str], list[dict[str, str]]]:
    with open(caminho, newline="", encoding="utf-8") as f:
        leitor = csv.reader(f)
        cabecalho = [c.strip() for c in next(leitor)]
        linhas = [dict(zip(cabecalho, (v.strip() for v in row))) for row in leitor if row]
    return cabecalho, linhas


def _num(v: str) -> float:
    try:
        return float(v)
    except ValueError:
        return math.nan


def comparar_results_csv(a: Path, b: Path, ignorar: tuple[str, ...] = COLUNAS_IGNORADAS_G2) -> ComparacaoResultados:
    """Igualdade EXATA (sem tolerância) de todas as colunas, exceto `ignorar`.
    NaN é tratado como igual a NaN. Cabeçalhos com espaços (versões antigas
    do Ultralytics) são normalizados."""
    cab_a, la = _ler_results(Path(a))
    cab_b, lb = _ler_results(Path(b))
    if cab_a != cab_b:
        return ComparacaoResultados(False, (len(la), len(lb)), [], motivo=f"Cabeçalhos diferentes: {cab_a} vs {cab_b}")
    colunas = [c for c in cab_a if c not in ignorar]
    if len(la) != len(lb):
        return ComparacaoResultados(False, (len(la), len(lb)), colunas, motivo="Número de épocas diferente")
    div: dict[str, dict] = {}
    for i, (ra, rb) in enumerate(zip(la, lb)):
        for c in colunas:
            x, y = _num(ra[c]), _num(rb[c])
            if (math.isnan(x) and math.isnan(y)) or x == y:
                continue
            d = div.setdefault(c, {"primeira_epoca": ra.get("epoch", str(i + 1)), "max_abs_diff": 0.0})
            if not (math.isnan(x) or math.isnan(y)):
                d["max_abs_diff"] = max(d["max_abs_diff"], abs(x - y))
            else:
                d["max_abs_diff"] = math.inf
    return ComparacaoResultados(not div, (len(la), len(lb)), colunas, div,
                                "" if not div else f"{len(div)} coluna(s) divergente(s)")


def comparar_pesos(last_a: Path, last_b: Path) -> dict:
    """Verificação ADICIONAL (informativa): compara os tensores dos pesos
    salvos (EMA, se houver; senão o modelo). Ignora metadados do
    checkpoint (data, versão, argumentos), que mudam entre execuções."""
    import torch  # import tardio

    def _estado(p):
        ck = torch.load(p, map_location="cpu", weights_only=False)
        m = ck.get("ema") if ck.get("ema") is not None else ck.get("model")
        return {k: v for k, v in m.float().state_dict().items()}

    ea, eb = _estado(last_a), _estado(last_b)
    if ea.keys() != eb.keys():
        return {"identico": False, "motivo": "conjuntos de tensores diferentes"}
    diferentes = [k for k in ea if not torch.equal(ea[k], eb[k])]
    return {"identico": not diferentes, "n_tensores": len(ea), "n_diferentes": len(diferentes),
            "exemplos": diferentes[:5]}


# ---------------------------------------------------------------------------
# G3 -- contagem REAL de iterações por callback
# ---------------------------------------------------------------------------

def _ambiente() -> dict:
    """GPU e versões: o determinismo bit a bit só vale no mesmo hardware e
    nas mesmas versões de biblioteca; registrar permite auditar isso."""
    info = {}
    try:
        import torch
        info["torch"] = torch.__version__
        info["gpu"] = torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
    except Exception:
        pass
    try:
        import ultralytics
        info["ultralytics"] = ultralytics.__version__
    except Exception:
        pass
    return info


class ContadorPassos:
    """Callbacks do Ultralytics: on_train_start registra o que o treinador
    montou; on_train_batch_end conta os lotes; on_train_end grava o JSON
    em `destino_json`. Uso: `ContadorPassos(dest).registrar(model)`."""

    def __init__(self, destino_json: Path):
        self.destino_json = Path(destino_json)
        self.passos = 0
        self.dados: dict = {}

    def on_train_start(self, trainer) -> None:
        loader = getattr(trainer, "train_loader", None)
        args = getattr(trainer, "args", None)
        self.passos = 0
        self.dados = {
            "n_imagens_dataset": len(loader.dataset) if loader is not None else None,
            "passos_por_epoca": len(loader) if loader is not None else None,
            "epochs": getattr(trainer, "epochs", None),
            "batch": getattr(trainer, "batch_size", None),
            "close_mosaic": getattr(args, "close_mosaic", None),
            "warmup_epochs": getattr(args, "warmup_epochs", None),
            "seed": getattr(args, "seed", None),
            "ambiente": _ambiente(),
        }

    def on_train_batch_end(self, trainer) -> None:
        self.passos += 1

    def on_train_end(self, trainer) -> None:
        self.dados["passos_executados"] = self.passos
        self.destino_json.parent.mkdir(parents=True, exist_ok=True)
        self.destino_json.write_text(json.dumps(self.dados, indent=2), encoding="utf-8")

    def registrar(self, model) -> "ContadorPassos":
        for evento in ("on_train_start", "on_train_batch_end", "on_train_end"):
            model.add_callback(evento, getattr(self, evento))
        return self


def verificar_passos(caminho_json: Path, orcamento: str) -> list[str]:
    """Lista de problemas (vazia = G3 aprovado quanto a passos)."""
    o = ORCAMENTOS[orcamento]
    esperado = {
        "n_imagens_dataset": COMPRIMENTO_LISTA,
        "passos_por_epoca": passos_por_epoca(COMPRIMENTO_LISTA),
        "epochs": o.epocas,
        "close_mosaic": o.close_mosaic,
        "passos_executados": o.passos_totais,
    }
    caminho_json = Path(caminho_json)
    if not caminho_json.exists():
        return [f"{caminho_json.name} ausente"]
    dados = json.loads(caminho_json.read_text(encoding="utf-8"))
    return [f"{k}: {dados.get(k)} != {v}" for k, v in esperado.items() if dados.get(k) != v]


# ---------------------------------------------------------------------------
# Pré-requisitos: amostra registrada e trainlists preparadas
# ---------------------------------------------------------------------------

def _sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(65536), b""):
            h.update(bloco)
    return h.hexdigest()


def verificar_pre_requisitos(repo: Path, dados_locais: Path) -> list[str]:
    """Antes de qualquer GPU: (1) o manifesto da amostra bate com o hash
    registrado em hashes.json; (2) as 3 trainlists existem com L = 5.392."""
    problemas = []
    repo, dados_locais = Path(repo), Path(dados_locais)
    manifesto = repo / "configs" / "amostra_sinteticas_fase5.csv"
    hashes = json.loads((repo / "docs" / "pre_registro" / "hashes.json").read_text(encoding="utf-8"))
    registrado = hashes.get("artefatos", {}).get("amostra_sinteticas_fase5.csv", {}).get("sha256")
    if not manifesto.exists():
        problemas.append("manifesto da amostra ausente")
    elif registrado is None:
        problemas.append("hash do manifesto não registrado em hashes.json")
    elif _sha256(manifesto) != registrado:
        problemas.append("manifesto da amostra diverge do hash registrado")
    contagens = dados_locais / "configs" / "contagens_f5.json"
    if not contagens.exists():
        problemas.append("contagens_f5.json ausente (rodar preparar_dados_locais_fase5)")
    else:
        c = json.loads(contagens.read_text(encoding="utf-8"))
        for braco in ("C", "M25", "M50"):
            if c.get(braco, {}).get("n_total") != COMPRIMENTO_LISTA:
                problemas.append(f"trainlist de {braco} sem n_total = {COMPRIMENTO_LISTA}")
            if not (dados_locais / "configs" / f"data_f5_{braco}.yaml").exists():
                problemas.append(f"data_f5_{braco}.yaml ausente")
    return problemas


# ---------------------------------------------------------------------------
# Veredito G2
# ---------------------------------------------------------------------------

def veredito_g2(results_a: Path, results_b: Path, passos_a: Path, passos_b: Path) -> dict:
    comp = comparar_results_csv(results_a, results_b)
    prob_a, prob_b = verificar_passos(passos_a, "S1"), verificar_passos(passos_b, "S1")
    go = comp.identico and not prob_a and not prob_b
    return {
        "veredito": "GO" if go else "NO-GO",
        "criterio": "adendo 3 §8 G2: results.csv idêntico em todas as colunas exceto time; G3 nas duas execuções",
        "results_identico": comp.identico,
        "n_linhas": list(comp.n_linhas),
        "colunas_comparadas": comp.colunas_comparadas,
        "divergencias": comp.divergencias,
        "motivo": comp.motivo,
        "g3_execucao_1": prob_a,
        "g3_execucao_2": prob_b,
    }

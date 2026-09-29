"""
Fase 5 -- desenho de passos igualados (adendo 3, lacrado no commit
3004384, tag `pre-registro-adendo3`).

Este módulo é a tradução LITERAL do adendo 3 em código:
- §4.1: orçamentos S1 (30 épocas) e S2 (75 épocas); frações 0, 0,25, 0,50;
- §4.2: comprimento de trainlist fixo L = 5.392 em todos os braços, com
  peso igual para todas as imagens reais;
- §4.4: warmup de 500 passos; close_mosaic = 1/15 das épocas; last.pt;
- §4.5: lista fechada de 30 execuções + 1 execução de portão (G2).

Nenhuma constante aqui pode mudar sem um novo adendo. Os testes em
`tests/test_passos_fixos.py` verificam cada número contra o texto lacrado.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from .executar import Execucao
from .protocol import ProtocoloTreinoV2, gerar_kwargs_treino

# --- §4.2 ---
N_REAIS_TREINO = 1348
COMPRIMENTO_LISTA = 5392
BATCH_SIZE = 16

# --- §4.4 ---
PESOS_BASE = "yolo11n.pt"
WARMUP_STEPS_ALVO = 500
FRACAO_CLOSE_MOSAIC = 15  # close_mosaic = épocas / 15

# --- §4.1 ---
FRACOES = {"C": 0.0, "M25": 0.25, "M50": 0.50}
BRACOS = tuple(FRACOES)

# --- §4.4 ---
SEEDS = (42, 123, 2024, 7, 31415)

PREFIXO = "f5"


class DesenhoInvalido(ValueError):
    """Alguma quantidade derivada não bate com o adendo 3."""


def passos_por_epoca(n_imagens: int, batch_size: int = BATCH_SIZE) -> int:
    """Iterações por época do dataloader do Ultralytics (drop_last=False)."""
    if n_imagens <= 0 or batch_size <= 0:
        raise ValueError("n_imagens e batch_size devem ser positivos")
    return math.ceil(n_imagens / batch_size)


@dataclass(frozen=True)
class Orcamento:
    nome: str
    epocas: int

    @property
    def close_mosaic(self) -> int:
        if self.epocas % FRACAO_CLOSE_MOSAIC:
            raise DesenhoInvalido(f"{self.nome}: {self.epocas} épocas não é múltiplo de {FRACAO_CLOSE_MOSAIC}.")
        return self.epocas // FRACAO_CLOSE_MOSAIC

    @property
    def passos_totais(self) -> int:
        return self.epocas * passos_por_epoca(COMPRIMENTO_LISTA)


ORCAMENTOS = {"S1": Orcamento("S1", 30), "S2": Orcamento("S2", 75)}


@dataclass(frozen=True)
class ComposicaoBraco:
    braco: str
    repeat_real: int
    n_sinteticas: int

    @property
    def n_total(self) -> int:
        return self.repeat_real * N_REAIS_TREINO + self.n_sinteticas

    @property
    def fracao_sintetica(self) -> float:
        return self.n_sinteticas / self.n_total


def composicao_braco(braco: str) -> ComposicaoBraco:
    """Deriva (repeat_real, n_sinteticas) da fração p e de L, exigindo que
    as reais caibam com peso inteiro e igual (§4.2)."""
    if braco not in FRACOES:
        raise DesenhoInvalido(f"Braço desconhecido: {braco}")
    n_sint = round(FRACOES[braco] * COMPRIMENTO_LISTA)
    vagas_reais = COMPRIMENTO_LISTA - n_sint
    if vagas_reais % N_REAIS_TREINO:
        raise DesenhoInvalido(f"{braco}: {vagas_reais} vagas reais não é múltiplo de {N_REAIS_TREINO}.")
    return ComposicaoBraco(braco, vagas_reais // N_REAIS_TREINO, n_sint)


@dataclass(frozen=True)
class ExecucaoF5:
    orcamento: str
    braco: str
    seed: int
    repeticao_portao: bool = False

    @property
    def rotulo_braco(self) -> str:
        """`f5_{S}_{braço}`; a repetição do portão G2 ganha o sufixo `_g2rep`
        para ter pasta própria e não ser tomada como "concluída"."""
        rotulo = f"{PREFIXO}_{self.orcamento}_{self.braco}"
        return f"{rotulo}_g2rep" if self.repeticao_portao else rotulo

    def como_execucao(self) -> Execucao:
        """Compatível com o executor retomável (src/train/executar.py)."""
        return Execucao(braco=self.rotulo_braco, seed=self.seed)

    @property
    def nome(self) -> str:
        return self.como_execucao().nome


def planejar_execucoes() -> list[ExecucaoF5]:
    """As 30 execuções de §4.5, em ordem: orçamento, seed, braço (os três
    braços de uma seed ficam juntos, para que uma interrupção de sessão não
    deixe um orçamento com braços desbalanceados por seed)."""
    return [
        ExecucaoF5(orc, braco, seed)
        for orc in ORCAMENTOS
        for seed in SEEDS
        for braco in BRACOS
    ]


def execucoes_portao_g2() -> tuple[ExecucaoF5, ExecucaoF5]:
    """G2 (§8): f5_S1_C_seed42 executado duas vezes. A primeira É a
    execução da lista fechada; a segunda é a repetição de portão."""
    return ExecucaoF5("S1", "C", 42), ExecucaoF5("S1", "C", 42, repeticao_portao=True)


def protocolo_orcamento(orcamento: str) -> ProtocoloTreinoV2:
    o = ORCAMENTOS[orcamento]
    return ProtocoloTreinoV2(
        pesos_base=PESOS_BASE,
        epochs_total=o.epocas,
        epoca_checkpoint=o.epocas,
        warmup_steps_alvo=WARMUP_STEPS_ALVO,
        batch_size=BATCH_SIZE,
        close_mosaic=o.close_mosaic,
    )


def kwargs_execucao(execucao: ExecucaoF5) -> dict:
    """Kwargs de treino. n_imagens_epoca é SEMPRE L = 5.392 (§4.2): todos
    os braços têm o mesmo comprimento de lista, logo o mesmo warmup em
    épocas, as mesmas épocas e o mesmo close_mosaic dentro do orçamento."""
    composicao_braco(execucao.braco)  # valida o braço
    kwargs = gerar_kwargs_treino(
        protocolo_orcamento(execucao.orcamento),
        n_imagens_epoca_deste_braco=COMPRIMENTO_LISTA,
        nome_braco=execucao.como_execucao().braco,
        seed=execucao.seed,
    )
    return kwargs


def diferencas_de_kwargs(a: dict, b: dict) -> set[str]:
    """Chaves cujo valor difere entre dois dicionários de kwargs."""
    return {k for k in set(a) | set(b) if a.get(k) != b.get(k)}

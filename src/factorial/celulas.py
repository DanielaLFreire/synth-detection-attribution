"""
Viabilidade das células do fatorial da Fase 3 (tarefa 3.2; adendo lacrado
em docs/pre_registro/adendo_fase3_fatorial.md, commit efd4699).

Desenho 3 × 2: escala {casada, reduzida, ampliada} × contraste {alto, baixo}.
Fontes elegíveis: SMD, SeaShips, ABOShips (InaTechShips excluído).

Definições (idênticas às já usadas no projeto -- verificadas no código):
- fator_reescala = area_caixa / area_nativa_do_crop (razão de ÁREAS,
  src/compose/compose.py linha 182; Fase 0; adendo §2).
- casada: fator em [0,5, 2,0]  <=> area_crop em [A/2, 2A]
- reduzida: fator < 0,5        <=> area_crop > 2A
- ampliada: fator > 2,0        <=> area_crop < A/2
- contraste alto: > mediana do pool elegível; baixo: <= mediana.

Uma caixa é VIÁVEL numa célula se, para cada uma das 3 fontes, existe ao
menos `minimo_por_fonte` crops elegíveis. Uma caixa entra no fatorial só
se for viável em TODAS as 6 células (mesmas caixas em todas, adendo §3.1).

Contagem por busca binária sobre as áreas ordenadas de cada (fonte, nível
de contraste): O(log n) por consulta.
"""
from __future__ import annotations

import bisect
from pathlib import Path
from dataclasses import dataclass, field

import numpy as np

FONTES_ELEGIVEIS = ["SMD", "SeaShips", "ABOShips"]
NIVEIS_ESCALA = ["casada", "reduzida", "ampliada"]
NIVEIS_CONTRASTE = ["alto", "baixo"]
FAIXA_CASADA = (0.5, 2.0)


@dataclass(frozen=True)
class CropElegivel:
    nome: str
    fonte: str
    area_px: float
    contraste: float


@dataclass(frozen=True)
class CaixaAlvo:
    imagem_id: str
    box_index: int
    area_px: float          # pixels NATIVOS da imagem -- usado para fator_reescala
    area_640_px: float | None = None  # referencial letterbox 640 (o que o detector vê) -- usado para geometria


def area_letterbox_640(area_nativa: float, largura_img: int, altura_img: int, lado: int = 640) -> float:
    """Converte área nativa para o referencial letterbox de `lado` px (mesmo
    método do perfil da Fase 0): fator = lado / max(W, H), área × fator²."""
    fator = lado / max(largura_img, altura_img, 1)
    return area_nativa * fator * fator


def nivel_escala(fator_reescala: float) -> str:
    lo, hi = FAIXA_CASADA
    if lo <= fator_reescala <= hi:
        return "casada"
    return "reduzida" if fator_reescala < lo else "ampliada"


def nivel_contraste(contraste: float, mediana: float) -> str:
    return "alto" if contraste > mediana else "baixo"


def _indexar_pool(pool: list[CropElegivel], mediana: float) -> dict[tuple[str, str], list[float]]:
    """{(fonte, nivel_contraste): areas ordenadas}."""
    indice: dict[tuple[str, str], list[float]] = {
        (f, c): [] for f in FONTES_ELEGIVEIS for c in NIVEIS_CONTRASTE
    }
    for crop in pool:
        if crop.fonte not in FONTES_ELEGIVEIS:
            continue
        indice[(crop.fonte, nivel_contraste(crop.contraste, mediana))].append(crop.area_px)
    for chave in indice:
        indice[chave].sort()
    return indice


def contar_elegiveis(area_caixa: float, areas_ordenadas: list[float], nivel: str) -> int:
    """Quantos crops (áreas ordenadas) caem no nível de escala para esta caixa."""
    lo, hi = FAIXA_CASADA
    a_min, a_max = area_caixa / hi, area_caixa / lo  # casada <=> area_crop em [A/2, 2A]
    if nivel == "casada":
        return bisect.bisect_right(areas_ordenadas, a_max) - bisect.bisect_left(areas_ordenadas, a_min)
    if nivel == "reduzida":
        return len(areas_ordenadas) - bisect.bisect_right(areas_ordenadas, a_max)
    if nivel == "ampliada":
        return bisect.bisect_left(areas_ordenadas, a_min)
    raise ValueError(nivel)


@dataclass
class ResultadoViabilidade:
    mediana_contraste: float
    minimo_por_fonte: int
    n_caixas_total: int
    caixas_viaveis: list[CaixaAlvo]
    caixas_excluidas: list[CaixaAlvo]
    # célula -> nº de caixas viáveis nela (antes da interseção)
    viaveis_por_celula: dict[str, int]
    # célula -> fonte -> menor contagem entre as caixas viáveis (gargalo)
    gargalo_por_celula_fonte: dict[str, dict[str, int]]
    pool_por_fonte_contraste: dict[str, int] = field(default_factory=dict)

    @property
    def fracao_viavel(self) -> float:
        return len(self.caixas_viaveis) / self.n_caixas_total if self.n_caixas_total else 0.0


def nome_celula(escala: str, contraste: str) -> str:
    return f"{escala}__{contraste}"


def verificar_viabilidade(
    caixas: list[CaixaAlvo],
    pool: list[CropElegivel],
    mediana_contraste: float | None = None,
    minimo_por_fonte: int = 1,
    niveis_escala: list[str] | None = None,
) -> ResultadoViabilidade:
    """`niveis_escala` permite avaliar um desenho com menos níveis (ex.:
    só casada/reduzida) -- adicionado em 2026-09-15 após a verificação
    mostrar que 'ampliada' é fisicamente impossível para caixas small."""
    niveis_escala = niveis_escala or NIVEIS_ESCALA
    elegiveis = [c for c in pool if c.fonte in FONTES_ELEGIVEIS]
    if mediana_contraste is None:
        mediana_contraste = float(np.median([c.contraste for c in elegiveis])) if elegiveis else 0.0
    indice = _indexar_pool(elegiveis, mediana_contraste)

    celulas = [nome_celula(e, c) for e in niveis_escala for c in NIVEIS_CONTRASTE]
    viaveis_por_celula = {cel: 0 for cel in celulas}
    gargalo = {cel: {f: None for f in FONTES_ELEGIVEIS} for cel in celulas}

    viaveis, excluidas = [], []
    for caixa in caixas:
        viavel_em_todas = True
        contagens_caixa: dict[str, dict[str, int]] = {}
        for e in niveis_escala:
            for c in NIVEIS_CONTRASTE:
                cel = nome_celula(e, c)
                contagens = {f: contar_elegiveis(caixa.area_px, indice[(f, c)], e) for f in FONTES_ELEGIVEIS}
                contagens_caixa[cel] = contagens
                ok = all(n >= minimo_por_fonte for n in contagens.values())
                if ok:
                    viaveis_por_celula[cel] += 1
                else:
                    viavel_em_todas = False
        if viavel_em_todas:
            viaveis.append(caixa)
            for cel, contagens in contagens_caixa.items():
                for f, n in contagens.items():
                    atual = gargalo[cel][f]
                    gargalo[cel][f] = n if atual is None else min(atual, n)
        else:
            excluidas.append(caixa)

    return ResultadoViabilidade(
        mediana_contraste=mediana_contraste,
        minimo_por_fonte=minimo_por_fonte,
        n_caixas_total=len(caixas),
        caixas_viaveis=viaveis,
        caixas_excluidas=excluidas,
        viaveis_por_celula=viaveis_por_celula,
        gargalo_por_celula_fonte={cel: {f: (v if v is not None else 0) for f, v in fs.items()} for cel, fs in gargalo.items()},
        pool_por_fonte_contraste={f"{f}__{c}": len(v) for (f, c), v in indice.items()},
    )


def comparar_geometria(viaveis: list[CaixaAlvo], excluidas: list[CaixaAlvo], limiar_small_px2: float = 32 * 32) -> dict:
    """Detecta exclusão sistemática: compara área mediana e fração 'small'
    (COCO: área < 32²) entre caixas mantidas e excluídas -- NO REFERENCIAL
    LETTERBOX 640 (o do detector e do perfil da Fase 0), quando disponível.
    CORREÇÃO 2026-09-15: a versão anterior usava a área nativa contra o
    limiar de 32², misturando referenciais (a fração small saía errada)."""
    def resumo(cs):
        if not cs:
            return {"n": 0, "area_mediana_nativa": None, "area_mediana_640": None, "fracao_small_640": None}
        nat = np.array([c.area_px for c in cs])
        tem_640 = all(c.area_640_px is not None for c in cs)
        a640 = np.array([c.area_640_px for c in cs]) if tem_640 else None
        return {
            "n": int(len(nat)),
            "area_mediana_nativa": float(np.median(nat)),
            "area_mediana_640": float(np.median(a640)) if tem_640 else None,
            "lado_mediano_640": float(np.sqrt(np.median(a640))) if tem_640 else None,
            "fracao_small_640": float(np.mean(a640 < limiar_small_px2)) if tem_640 else None,
        }
    return {"referencial": "letterbox_640", "viaveis": resumo(viaveis), "excluidas": resumo(excluidas)}


# ---------------------------------------------------------------------------
# Limpeza pós-composição: sintéticas sem nenhuma colagem são cópias do real
# ---------------------------------------------------------------------------

def imagens_com_colagem(manifesto_csv: Path) -> set[str]:
    """Conjunto de `imagem_id` que receberam ao menos uma colagem, pelo manifesto."""
    import csv
    with open(manifesto_csv, newline="", encoding="utf-8") as f:
        return {l["imagem_id"] for l in csv.DictReader(f)}


def remover_sinteticas_sem_colagem(pasta_imagens: Path, pasta_labels: Path, manifesto_csv: Path) -> int:
    """Remove as saídas `{imagem_id}_v{k}.png/.txt` de imagens sem nenhuma
    colagem (cópias idênticas do real, geradas pelo compositor quando
    nenhuma caixa da imagem é viável). Retorna quantas imagens foram
    removidas. Mantém o N sintético igual ao pré-registrado (adendo 2 §3.5)."""
    com_colagem = imagens_com_colagem(manifesto_csv)
    removidas = 0
    for p in sorted(Path(pasta_imagens).glob("*_v*.png")):
        imagem_id = p.stem.rsplit("_v", 1)[0]
        if imagem_id not in com_colagem:
            p.unlink()
            label = Path(pasta_labels) / f"{p.stem}.txt"
            if label.exists():
                label.unlink()
            removidas += 1
    return removidas

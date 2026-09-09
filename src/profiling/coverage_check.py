"""
Verificação de cobertura do reservatório para o fatorial do Estágio B
(tarefa 0.3, §9 do plano).

Objetivo: antes de desenhar as células do fatorial (§5.7), confirmar que
cada fonte tem reservatório suficiente para contribuir, em proporção
comparável, a cada nível do fator "compatibilidade de escala" (casada vs.
descasada) -- sem essa checagem, uma fonte com distribuição de tamanho
nativo muito diferente do alvo (ex.: InaTechShips, mediana 358px, vs.
alvo com caixas tipicamente <100px) poderia ficar estruturalmente incapaz
de contribuir à célula "casada" na mesma proporção que as outras fontes,
reintroduzindo o confound de fonte que o desenho do Estágio B existe para
eliminar (ver docs/CHANGELOG_metodologico.md).

Método: simulação de pareamento aleatório (crop de origem × caixa de
destino), calculando fator_reescala = área_destino / área_original para
cada par simulado -- mesma fórmula já usada em src/compose/compose.py.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path

from PIL import Image


@dataclass
class ResultadoSimulacaoEscala:
    fonte: str
    n_amostras: int
    pct_casada: float           # fator_reescala dentro da faixa "casada"
    pct_descasada_downscale: float  # fator_reescala abaixo da faixa (crop precisa encolher muito)
    pct_descasada_upscale: float    # fator_reescala acima da faixa (crop precisa esticar muito)


def obter_tamanhos_absolutos_alvo(imagens_dir: Path, labels_dir: Path) -> list[tuple[int, int]]:
    """Lê os labels YOLO do dataset-alvo e retorna a lista de dimensões
    ABSOLUTAS (largura_px, altura_px) de cada caixa -- mesma lógica de
    conversão já usada em src/profiling/target_profile.py e
    src/compose/compose.py, aqui retornando a lista bruta em vez de
    estatísticas agregadas, porque a simulação precisa amostrar
    individualmente."""
    imagens_dir, labels_dir = Path(imagens_dir), Path(labels_dir)
    tamanhos: list[tuple[int, int]] = []

    for caminho_label in sorted(labels_dir.glob("*.txt")):
        imagem_id = caminho_label.stem
        caminho_imagem = None
        for ext in (".png", ".jpg", ".jpeg"):
            candidato = imagens_dir / f"{imagem_id}{ext}"
            if candidato.exists():
                caminho_imagem = candidato
                break
        if caminho_imagem is None:
            continue

        with Image.open(caminho_imagem) as img:
            largura_img, altura_img = img.size

        with open(caminho_label, "r", encoding="utf-8") as f:
            for linha in f:
                partes = linha.split()
                if len(partes) < 5:
                    continue
                _, cx, cy, w, h = partes[:5]
                bw_px = round(float(w) * largura_img)
                bh_px = round(float(h) * altura_img)
                if bw_px > 0 and bh_px > 0:
                    tamanhos.append((bw_px, bh_px))

    return tamanhos


def simular_compatibilidade_escala(
    fonte: str,
    tamanhos_origem: list[tuple[int, int]],
    tamanhos_destino: list[tuple[int, int]],
    n_amostras: int = 5000,
    faixa_casada: tuple[float, float] = (0.5, 2.0),
    seed: int = 42,
) -> ResultadoSimulacaoEscala:
    """Simula n_amostras pareamentos aleatórios (crop desta fonte × caixa
    de destino do alvo) e classifica cada um pelo fator_reescala
    resultante -- mesma fórmula do componente de composição real."""
    if not tamanhos_origem or not tamanhos_destino:
        return ResultadoSimulacaoEscala(fonte, 0, 0.0, 0.0, 0.0)

    rng = random.Random(seed)
    n_casada = n_downscale = n_upscale = 0

    for _ in range(n_amostras):
        lo, ao = rng.choice(tamanhos_origem)
        ld, ad = rng.choice(tamanhos_destino)
        area_origem = lo * ao
        area_destino = ld * ad
        if area_origem <= 0:
            continue
        fator_reescala = area_destino / area_origem

        if faixa_casada[0] <= fator_reescala <= faixa_casada[1]:
            n_casada += 1
        elif fator_reescala < faixa_casada[0]:
            n_downscale += 1
        else:
            n_upscale += 1

    return ResultadoSimulacaoEscala(
        fonte=fonte,
        n_amostras=n_amostras,
        pct_casada=100 * n_casada / n_amostras,
        pct_descasada_downscale=100 * n_downscale / n_amostras,
        pct_descasada_upscale=100 * n_upscale / n_amostras,
    )

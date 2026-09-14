"""
Features baseadas em CLIP (Família 4, §6 do plano) -- a matemática, em
CPU e testável. A extração dos embeddings (GPU) fica no script.

- `dist_clip_alvo`: 1 - cosseno(embedding do crop, centroide dos
  embeddings dos objetos REAIS do alvo). Quanto maior, mais a aparência
  do crop se afasta do domínio-alvo.
- `novidade_pool`: 1 - cosseno(embedding do crop, vizinho mais próximo
  no pool, EXCLUINDO o próprio crop). Quanto maior, mais "único" o crop
  é dentro do pool (baixo = redundante).

Operacionalização registrada (2026-09-14): os crops do pool são embutidos
a partir do RGB RETANGULAR original (descartando o alpha da máscara --
o RGB fora da máscara foi preservado na extração, verificado em
`aplicar_mascara_e_recortar`), e os objetos reais do alvo a partir do
recorte retangular da caixa anotada. Ambos incluem o fundo ao redor do
objeto: comparação like-with-like. Consequência: `dist_clip_alvo` mede
similaridade de aparência do objeto+contexto, não do objeto isolado.

Vizinho mais próximo em blocos: a matriz completa (86k × 86k) não cabe
em memória; processa-se em blocos de linhas contra o pool inteiro.
"""
from __future__ import annotations

import numpy as np


def normalizar_l2(emb: np.ndarray) -> np.ndarray:
    """Normaliza cada linha para norma 1 (cosseno vira produto escalar)."""
    emb = np.asarray(emb, dtype=np.float32)
    normas = np.linalg.norm(emb, axis=1, keepdims=True)
    normas[normas == 0] = 1.0
    return emb / normas


def centroide_normalizado(emb_alvo: np.ndarray) -> np.ndarray:
    """Média dos embeddings (já normalizados) do alvo, renormalizada."""
    c = normalizar_l2(emb_alvo).mean(axis=0)
    n = np.linalg.norm(c)
    return c / n if n > 0 else c


def dist_clip_alvo(emb_crops: np.ndarray, emb_alvo: np.ndarray) -> np.ndarray:
    """1 - cosseno ao centroide do alvo, para cada crop."""
    c = centroide_normalizado(emb_alvo)
    return 1.0 - normalizar_l2(emb_crops) @ c


def novidade_pool(emb_pool: np.ndarray, tamanho_bloco: int = 2048) -> tuple[np.ndarray, np.ndarray]:
    """Para cada crop do pool: 1 - cosseno ao vizinho mais próximo,
    excluindo ele mesmo. Retorna (novidade, indice_do_vizinho)."""
    E = normalizar_l2(emb_pool)
    n = E.shape[0]
    novidade = np.empty(n, dtype=np.float32)
    vizinho = np.empty(n, dtype=np.int64)
    for ini in range(0, n, tamanho_bloco):
        fim = min(ini + tamanho_bloco, n)
        sim = E[ini:fim] @ E.T                       # (bloco, n)
        idx_linhas = np.arange(fim - ini)
        sim[idx_linhas, np.arange(ini, fim)] = -np.inf  # exclui o próprio crop
        melhor = sim.argmax(axis=1)
        vizinho[ini:fim] = melhor
        novidade[ini:fim] = 1.0 - sim[idx_linhas, melhor]
    return novidade, vizinho

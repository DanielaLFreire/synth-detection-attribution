"""
Features do Estágio A computáveis em CPU (Famílias 1, 2 e 3 do §6 do plano).

Excluídas deliberadamente desta etapa (exigem CLIP -- uma passada de GPU
decidida separadamente, depois de avaliar o modelo com estas features):
`dist_clip_alvo`, `novidade_pool`.

Três decisões de desenho registradas em docs/CHANGELOG_metodologico.md:
1. `distorcao_aspect`: o composer redimensiona o crop para as dimensões
   EXATAS da caixa de destino, ignorando a proporção original do crop --
   deformação real, extraída aqui como feature (log da razão de aspectos;
   0 = sem deformação).
2. `cobertura_mascara` recalculada direto do canal alpha do arquivo do
   crop (fração de pixels com alpha > 0) -- equivalente ao registrado no
   manifesto de extração, sem join frágil por nome de arquivo.
3. Nitidez e contraste medidos SÓ dentro da máscara (alpha > 0) -- medir
   no retângulo inteiro criaria arestas falsas na fronteira
   transparente/opaco, inflando a nitidez artificialmente.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image


# ---------------------------------------------------------------------------
# Família 2/3: geometria e transformação -- puras, a partir do manifesto
# ---------------------------------------------------------------------------

def calcular_features_geometricas(linha: dict) -> dict:
    """A partir de uma linha do manifesto de composição (já com os campos
    de caixa/crop/imagem), calcula as features geométricas e de
    transformação. Função pura, testável."""
    x0, y0 = float(linha["caixa_x0_px"]), float(linha["caixa_y0_px"])
    x1, y1 = float(linha["caixa_x1_px"]), float(linha["caixa_y1_px"])
    largura_img = float(linha["imagem_largura_px"])
    altura_img = float(linha["imagem_altura_px"])
    bw = max(1.0, x1 - x0)
    bh = max(1.0, y1 - y0)

    crop_w = max(1.0, float(linha["crop_largura_original_px"]))
    crop_h = max(1.0, float(linha["crop_altura_original_px"]))

    aspect_caixa = bw / bh
    aspect_crop = crop_w / crop_h
    fator_reescala = float(linha["fator_reescala"])

    return {
        "pos_h": (x0 + x1) / 2 / largura_img,          # centro horizontal normalizado
        "pos_v": (y0 + y1) / 2 / altura_img,           # centro vertical normalizado
        "area_caixa_norm": (bw * bh) / (largura_img * altura_img),
        "menor_lado_caixa_px": min(bw, bh),
        "aspect_caixa": aspect_caixa,
        "aspect_crop_original": aspect_crop,
        "distorcao_aspect": math.log(aspect_caixa / aspect_crop),   # 0 = sem deformação
        "log_fator_reescala": math.log(max(fator_reescala, 1e-9)),  # 0 = escala casada
        "crop_menor_lado_original_px": min(crop_w, crop_h),
        "upsample": 1 if fator_reescala > 1.0 else 0,
    }


# ---------------------------------------------------------------------------
# Família 3: coerência escala x posição, ajustada nos dados REAIS do alvo
# ---------------------------------------------------------------------------

@dataclass
class RegressaoEscalaPosicao:
    """log(area_norm) = a + b * pos_v, ajustada por mínimos quadrados nas
    caixas reais do alvo. Resíduo = quanto uma caixa foge da relação
    típica de perspectiva (objetos mais baixos no quadro tendem a ser
    maiores)."""
    a: float
    b: float

    def residuo(self, pos_v: float, area_norm: float) -> float:
        previsto = self.a + self.b * pos_v
        return math.log(max(area_norm, 1e-12)) - previsto


def ajustar_regressao_escala_posicao(pos_v: list[float], area_norm: list[float]) -> RegressaoEscalaPosicao:
    """Mínimos quadrados simples (numpy), sem dependência de sklearn."""
    x = np.asarray(pos_v, dtype=float)
    y = np.log(np.maximum(np.asarray(area_norm, dtype=float), 1e-12))
    if len(x) < 2 or np.allclose(x, x[0]):
        return RegressaoEscalaPosicao(a=float(y.mean()) if len(y) else 0.0, b=0.0)
    b, a = np.polyfit(x, y, deg=1)
    return RegressaoEscalaPosicao(a=float(a), b=float(b))


def caixas_reais_do_alvo(labels_dir: Path) -> tuple[list[float], list[float]]:
    """Lê labels YOLO reais (normalizados) e devolve (pos_v, area_norm)
    de cada caixa -- em coordenadas normalizadas, sem precisar abrir a
    imagem. Usado para ajustar a regressão de coerência."""
    pos_v, area_norm = [], []
    for caminho in sorted(Path(labels_dir).glob("*.txt")):
        with open(caminho, "r", encoding="utf-8") as f:
            for linha in f:
                partes = linha.split()
                if len(partes) < 5:
                    continue
                _, cx, cy, w, h = partes[:5]
                pos_v.append(float(cy))
                area_norm.append(float(w) * float(h))
    return pos_v, area_norm


# ---------------------------------------------------------------------------
# Família 1: intrínsecas do crop -- processamento de imagem
# ---------------------------------------------------------------------------

def _laplaciano(cinza: np.ndarray) -> np.ndarray:
    """Laplaciano 3x3 (kernel [0,1,0;1,-4,1;0,1,0]) via numpy, sem cv2/scipy.
    Bordas: descarta 1 pixel de margem (retorna array menor)."""
    c = cinza.astype(float)
    return (c[:-2, 1:-1] + c[2:, 1:-1] + c[1:-1, :-2] + c[1:-1, 2:] - 4.0 * c[1:-1, 1:-1])


def calcular_features_intrinsecas(caminho_crop: Path) -> dict:
    """Nitidez (variância do Laplaciano), contraste (desvio padrão),
    brilho médio e cobertura da máscara -- tudo medido SÓ dentro da
    máscara (alpha > 0), para não contar arestas falsas da fronteira
    transparente/opaco. Crops sem canal alpha (modo retangular) são
    tratados como máscara cheia."""
    with Image.open(caminho_crop) as img:
        rgba = np.asarray(img.convert("RGBA"))

    rgb = rgba[:, :, :3].astype(float)
    alpha = rgba[:, :, 3]
    mascara = alpha > 0
    cobertura = float(mascara.mean()) if mascara.size else 0.0

    cinza = 0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]

    if mascara.sum() < 4 or cinza.shape[0] < 3 or cinza.shape[1] < 3:
        return {"nitidez": 0.0, "contraste": 0.0, "brilho_medio": 0.0, "cobertura_mascara": cobertura}

    lap = _laplaciano(cinza)
    mascara_interna = mascara[1:-1, 1:-1]
    # descarta também a fronteira da máscara: só pixels cujos 4 vizinhos estão dentro
    vizinhos_dentro = (mascara[:-2, 1:-1] & mascara[2:, 1:-1] & mascara[1:-1, :-2] & mascara[1:-1, 2:])
    interior = mascara_interna & vizinhos_dentro

    nitidez = float(lap[interior].var()) if interior.sum() >= 2 else 0.0
    valores_cinza = cinza[mascara]
    contraste = float(valores_cinza.std())
    brilho = float(valores_cinza.mean())

    return {"nitidez": nitidez, "contraste": contraste, "brilho_medio": brilho, "cobertura_mascara": cobertura}

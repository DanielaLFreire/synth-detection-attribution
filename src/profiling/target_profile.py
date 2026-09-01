"""
Perfilamento estrutural canônico do dataset-alvo (tarefa 0.1, §9 do plano).

Método de classificação de tamanho (small/medium/large): letterbox --
calcula um único fator de escala s = eval_size / max(W, H) a partir das
dimensões REAIS de cada imagem, aplicado igualmente aos dois eixos. Este é
o método correto porque reflete o pré-processamento real de treino (YOLO
redimensiona preservando proporção, nunca "estica" para um quadrado).

Decisão fechada em docs/CHANGELOG_metodologico.md (2026-09-01), após
encontrar e explicar uma divergência entre duas medições legadas do mesmo
indicador no CITRA-3D-Real (71,6% vs. 82,2% small) -- causa raiz: um script
anterior (`analisar_escala_citra3d.py`) multiplicava largura e altura
normalizadas por 640 independentemente, equivalente a assumir imagem
quadrada. Confirmado empiricamente que as imagens do CITRA-3D-Real NÃO são
quadradas (1920x1061 / 1920x1080, amostra verificada via PIL).

Limiares de tamanho: Lin, T.-Y. et al. (2014). "Microsoft COCO: Common
Objects in Context." ECCV 2014. (small < 32² px, medium < 96² px, large >= 96² px)
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image

LIMIAR_SMALL_PX = 32
LIMIAR_MEDIUM_PX = 96
EVAL_SIZE_PADRAO = 640


@dataclass
class CaixaPerfil:
    imagem_id: str
    largura_norm: float
    altura_norm: float
    area_norm: float
    aspect_ratio: float
    x_center_norm: float
    y_center_norm: float
    categoria_tamanho: str  # "small" | "medium" | "large" -- método letterbox


def _percentil(valores: list[float], p: float) -> float:
    """Percentil sem dependência de numpy -- interpolação linear simples,
    suficiente para relatório descritivo (não é usado em teste estatístico
    formal, que terá seu próprio tratamento na Fase 1)."""
    if not valores:
        return float("nan")
    valores_ordenados = sorted(valores)
    k = (len(valores_ordenados) - 1) * (p / 100)
    f, c = int(k), min(int(k) + 1, len(valores_ordenados) - 1)
    if f == c:
        return valores_ordenados[f]
    return valores_ordenados[f] + (valores_ordenados[c] - valores_ordenados[f]) * (k - f)


def classificar_tamanho_letterbox(
    largura_norm: float, altura_norm: float, largura_img: int, altura_img: int,
    eval_size: int = EVAL_SIZE_PADRAO,
) -> str:
    """Classifica small/medium/large simulando o redimensionamento
    letterbox real (fator de escala único a partir da dimensão real da
    imagem), não um stretch para quadrado."""
    bw_px_original = largura_norm * largura_img
    bh_px_original = altura_norm * altura_img
    s = eval_size / max(largura_img, altura_img)
    bw_letterbox = bw_px_original * s
    bh_letterbox = bh_px_original * s
    area_letterbox_px2 = bw_letterbox * bh_letterbox

    if area_letterbox_px2 < LIMIAR_SMALL_PX ** 2:
        return "small"
    if area_letterbox_px2 < LIMIAR_MEDIUM_PX ** 2:
        return "medium"
    return "large"


def perfilar_dataset(
    imagens_dir: Path, labels_dir: Path, eval_size: int = EVAL_SIZE_PADRAO,
) -> dict:
    """Perfila um split (imagens + labels YOLO), retornando estatísticas
    descritivas por percentil e a distribuição COCO-style small/medium/large
    calculada pelo método letterbox."""
    imagens_dir, labels_dir = Path(imagens_dir), Path(labels_dir)
    caixas: list[CaixaPerfil] = []
    objetos_por_imagem: list[int] = []

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

        n_objetos_nesta_imagem = 0
        with open(caminho_label, "r", encoding="utf-8") as f:
            for linha in f:
                partes = linha.split()
                if len(partes) < 5:
                    continue
                _, cx, cy, w, h = partes[:5]
                w, h, cx, cy = float(w), float(h), float(cx), float(cy)
                categoria = classificar_tamanho_letterbox(w, h, largura_img, altura_img, eval_size)
                caixas.append(CaixaPerfil(
                    imagem_id=imagem_id, largura_norm=w, altura_norm=h,
                    area_norm=w * h, aspect_ratio=(w / h) if h > 0 else float("nan"),
                    x_center_norm=cx, y_center_norm=cy, categoria_tamanho=categoria,
                ))
                n_objetos_nesta_imagem += 1
        if n_objetos_nesta_imagem > 0:
            objetos_por_imagem.append(n_objetos_nesta_imagem)

    n = len(caixas)
    contagem_categorias = {"small": 0, "medium": 0, "large": 0}
    for c in caixas:
        contagem_categorias[c.categoria_tamanho] += 1

    def stats(valores: list[float]) -> dict:
        if not valores:
            return {}
        return {
            "count": len(valores),
            "mean": sum(valores) / len(valores),
            "median": _percentil(valores, 50),
            "min": min(valores), "max": max(valores),
            "p5": _percentil(valores, 5), "p10": _percentil(valores, 10),
            "p25": _percentil(valores, 25), "p75": _percentil(valores, 75),
            "p90": _percentil(valores, 90), "p95": _percentil(valores, 95),
        }

    return {
        "metodo_classificacao_tamanho": "letterbox",
        "eval_size": eval_size,
        "limiar_small_px": LIMIAR_SMALL_PX,
        "limiar_medium_px": LIMIAR_MEDIUM_PX,
        "referencia_limiares": "Lin et al. (2014), Microsoft COCO: Common Objects in Context, ECCV",
        "n_bboxes_total": n,
        "n_imagens": len(objetos_por_imagem),
        "coco_size_distribution": {
            "small_count": contagem_categorias["small"],
            "medium_count": contagem_categorias["medium"],
            "large_count": contagem_categorias["large"],
            "small_pct": 100 * contagem_categorias["small"] / n if n else 0,
            "medium_pct": 100 * contagem_categorias["medium"] / n if n else 0,
            "large_pct": 100 * contagem_categorias["large"] / n if n else 0,
        },
        "width_normalized": stats([c.largura_norm for c in caixas]),
        "height_normalized": stats([c.altura_norm for c in caixas]),
        "area_normalized": stats([c.area_norm for c in caixas]),
        "aspect_ratio": stats([c.aspect_ratio for c in caixas]),
        "x_center": stats([c.x_center_norm for c in caixas]),
        "y_center": stats([c.y_center_norm for c in caixas]),
        "objects_per_image": stats([float(x) for x in objetos_por_imagem]),
    }

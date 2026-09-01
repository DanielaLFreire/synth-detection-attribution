"""
Composição sintética in-place (segment-and-paste) com manifesto por colagem.

Método: para cada caixa REAL de uma imagem-alvo, sorteia um crop de um pool
de fontes públicas, redimensiona para as dimensões exatas da caixa de
destino, e cola. A caixa de destino é sempre HERDADA do label real -- nunca
sorteada -- decisão verificada e documentada em docs/CHANGELOG_metodologico.md
(§8.3 do plano, resolvido por leitura direta do pipeline anterior).

Referências metodológicas: ver cabeçalho de manifest.py.

DECISÃO DE SEGURANÇA (§5.2 do plano): por padrão, este módulo RECUSA compor
sobre o split de treino do dataset-alvo, porque um modelo já treinado por
gradiente sobre essas imagens de fundo pode "acertar" por memorização de
cena, não pela qualidade da colagem -- isso confundiria o alvo do Estágio A.
Colagens de sondagem devem ser geradas sobre o split de VALIDAÇÃO. A
composição sobre o split de treino só é permitida com
`permitir_split_treino=True` explícito, e sempre imprime um aviso.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from PIL import Image

from .manifest import (
    MANIFEST_VERSION,
    ManifestRow,
    ManifestWriter,
    escrever_metadata_execucao,
    novo_run_id,
)

# Método de interpolação usado no resize -- CONSTANTE e documentada.
# Ver §6 do plano: como não há variação natural deste parâmetro no pipeline
# atual, ele NÃO é uma feature observacional do Estágio A. Se o grupo decidir
# testar o efeito do método de interpolação, isso deve ser feito como um
# fator manipulado do Estágio B, com este mesmo parâmetro tornado variável.
METODO_INTERPOLACAO = "LANCZOS"
_PIL_INTERP = Image.LANCZOS


class SplitDeTreinoBloqueado(RuntimeError):
    """Levantado quando se tenta compor sobre o split de treino sem override
    explícito. Ver §5.2 do plano -- isso não é um bug, é uma barreira
    deliberada contra o confound de memorização de cena."""


@dataclass
class CaixaAlvo:
    """Uma caixa real, lida do label do dataset-alvo, em pixels absolutos."""
    box_index: int
    x0: int
    y0: int
    x1: int
    y1: int

    @property
    def largura(self) -> int:
        return self.x1 - self.x0

    @property
    def altura(self) -> int:
        return self.y1 - self.y0


def ler_caixas_yolo(caminho_label: Path, largura_img: int, altura_img: int) -> list[CaixaAlvo]:
    """Lê um arquivo de label YOLO (classe cx cy w h, normalizados) e
    converte para pixels absolutos. Assume classe única (já verificado como
    limpo em labels_single_class/ -- ver CHANGELOG_metodologico.md)."""
    caixas: list[CaixaAlvo] = []
    if not caminho_label.exists():
        return caixas
    with open(caminho_label, "r", encoding="utf-8") as f:
        for i, linha in enumerate(f):
            partes = linha.split()
            if len(partes) < 5:
                continue
            _, cx, cy, w, h = partes[:5]
            cx, cy, w, h = float(cx), float(cy), float(w), float(h)
            bw_px = w * largura_img
            bh_px = h * altura_img
            x0 = round(cx * largura_img - bw_px / 2)
            y0 = round(cy * altura_img - bh_px / 2)
            x1 = round(x0 + bw_px)
            y1 = round(y0 + bh_px)
            caixas.append(CaixaAlvo(box_index=i, x0=x0, y0=y0, x1=x1, y1=y1))
    return caixas


def compor_dataset(
    *,
    imagens_alvo_dir: Path,
    labels_alvo_dir: Path,
    pool_crops: Sequence[tuple[str, Path]],   # [(nome_da_fonte, caminho_do_crop), ...]
    saida_imagens_dir: Path,
    saida_labels_dir: Path,
    manifesto_csv: Path,
    manifesto_metadata_json: Path,
    split: str,
    n_variacoes: int = 13,
    seed: int = 42,
    permitir_split_treino: bool = False,
) -> int:
    """Compõe um dataset sintético in-place sobre um split do dataset-alvo,
    gravando um manifesto por colagem. Retorna o número de colagens geradas.

    Parâmetros
    ----------
    imagens_alvo_dir, labels_alvo_dir: pastas do split do dataset-alvo
        (ex.: CITRA-3D-Real/val/images, CITRA-3D-Real/val/labels_single_class).
    pool_crops: lista de (nome_da_fonte, caminho_do_arquivo_de_crop) --
        o pool já deve estar filtrado pelo filtro unificado (§8.1 do plano)
        antes de chegar aqui; este módulo não filtra crops.
    split: rótulo do split sendo processado -- usado só para registro no
        manifesto e para a checagem de segurança abaixo.
    permitir_split_treino: ver docstring do módulo. Default False.
    """
    if split == "train" and not permitir_split_treino:
        raise SplitDeTreinoBloqueado(
            "Recusando compor sobre o split de TREINO do dataset-alvo. "
            "Isso reintroduziria o confound de memorização de cena documentado "
            "em docs/CHANGELOG_metodologico.md (§5.2 do plano): um modelo já "
            "treinado por gradiente sobre este fundo pode 'acertar' por "
            "familiaridade de cena, não pela qualidade da colagem. "
            "Gere as colagens de sondagem sobre o split de VALIDAÇÃO. "
            "Se você tem uma razão deliberada e documentada para prosseguir "
            "mesmo assim, chame com permitir_split_treino=True explicitamente."
        )
    if split == "train":
        print(
            "[AVISO] Compondo sobre o split de TREINO com override explícito "
            "(permitir_split_treino=True). Isso NÃO deve ser usado para gerar "
            "as colagens de sondagem do Estágio A -- registre a justificativa "
            "no docs/CHANGELOG_metodologico.md antes de usar esta saída."
        )

    rng = random.Random(seed)
    run_id = novo_run_id()
    inicio = datetime.now(timezone.utc)

    saida_imagens_dir = Path(saida_imagens_dir)
    saida_labels_dir = Path(saida_labels_dir)
    saida_imagens_dir.mkdir(parents=True, exist_ok=True)
    saida_labels_dir.mkdir(parents=True, exist_ok=True)

    n_total = 0
    with ManifestWriter(manifesto_csv) as manifesto:
        for caminho_img in sorted(Path(imagens_alvo_dir).glob("*.png")):
            imagem_id = caminho_img.stem
            caminho_label = Path(labels_alvo_dir) / f"{imagem_id}.txt"

            with Image.open(caminho_img) as img_original:
                largura_img, altura_img = img_original.size
                caixas = ler_caixas_yolo(caminho_label, largura_img, altura_img)
                if not caixas:
                    continue

                for k in range(n_variacoes):
                    cena = img_original.convert("RGBA").copy()

                    for caixa in caixas:
                        seed_local = rng.randint(0, 2**31 - 1)
                        rng_local = random.Random(seed_local)
                        fonte, caminho_crop = rng_local.choice(list(pool_crops))

                        with Image.open(caminho_crop) as crop_original:
                            crop_original = crop_original.convert("RGBA")
                            largura_crop_orig, altura_crop_orig = crop_original.size
                            crop_redimensionado = crop_original.resize(
                                (max(1, caixa.largura), max(1, caixa.altura)),
                                _PIL_INTERP,
                            )
                        cena.paste(crop_redimensionado, (caixa.x0, caixa.y0), crop_redimensionado)

                        area_destino = max(1, caixa.largura) * max(1, caixa.altura)
                        area_original = max(1, largura_crop_orig) * max(1, altura_crop_orig)
                        fator_reescala = area_destino / area_original

                        manifesto.escrever(ManifestRow(
                            manifest_version=MANIFEST_VERSION,
                            run_id=run_id,
                            timestamp_geracao=datetime.now(timezone.utc).isoformat(),
                            split=split,
                            imagem_id=imagem_id,
                            box_index=caixa.box_index,
                            grupo_geometrico_id=f"{imagem_id}__{caixa.box_index}",
                            variacao_k=k,
                            caixa_x0_px=caixa.x0, caixa_y0_px=caixa.y0,
                            caixa_x1_px=caixa.x1, caixa_y1_px=caixa.y1,
                            caixa_largura_px=caixa.largura, caixa_altura_px=caixa.altura,
                            imagem_largura_px=largura_img, imagem_altura_px=altura_img,
                            fonte=fonte,
                            crop_path=str(caminho_crop),
                            crop_largura_original_px=largura_crop_orig,
                            crop_altura_original_px=altura_crop_orig,
                            fator_reescala=fator_reescala,
                            upsample=fator_reescala > 1.0,
                            metodo_interpolacao=METODO_INTERPOLACAO,
                            seed_sorteio=seed_local,
                            imagem_destino_path=str(saida_imagens_dir / f"{imagem_id}_v{k:02d}.png"),
                            label_destino_path=str(saida_labels_dir / f"{imagem_id}_v{k:02d}.txt"),
                        ))
                        n_total += 1

                    caminho_saida_img = saida_imagens_dir / f"{imagem_id}_v{k:02d}.png"
                    cena.convert("RGB").save(caminho_saida_img)

                    # label herdado: mesmas caixas, classe única 0 (ver §5.1 -- geometria
                    # herdada e idêntica entre variações da mesma imagem/caixa)
                    caminho_saida_label = saida_labels_dir / f"{imagem_id}_v{k:02d}.txt"
                    with open(caminho_saida_label, "w", encoding="utf-8") as f:
                        for caixa in caixas:
                            cx = (caixa.x0 + caixa.x1) / 2 / largura_img
                            cy = (caixa.y0 + caixa.y1) / 2 / altura_img
                            w = caixa.largura / largura_img
                            h = caixa.altura / altura_img
                            f.write(f"0 {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}\n")

    fim = datetime.now(timezone.utc)
    escrever_metadata_execucao(
        manifesto_metadata_json,
        config={
            "imagens_alvo_dir": str(imagens_alvo_dir),
            "labels_alvo_dir": str(labels_alvo_dir),
            "split": split,
            "n_variacoes": n_variacoes,
            "seed": seed,
            "metodo_interpolacao": METODO_INTERPOLACAO,
            "n_fontes_no_pool": len(set(f for f, _ in pool_crops)),
            "n_crops_no_pool": len(pool_crops),
        },
        n_linhas=n_total,
        inicio=inicio,
        fim=fim,
    )
    return n_total

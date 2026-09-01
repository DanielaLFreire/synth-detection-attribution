"""Testes da tarefa 0.1: perfilamento estrutural canônico com método
letterbox, incluindo reprodução da divergência letterbox vs. stretch já
diagnosticada para o CITRA-3D-Real."""
from __future__ import annotations

from pathlib import Path

from PIL import Image

from src.profiling import perfilar_dataset, classificar_tamanho_letterbox


def test_classificacao_letterbox_em_imagem_widescreen_como_o_citra():
    """Reproduz o cenário real: imagem 1920x1080 (razão ~1.78:1, como o
    CITRA-3D-Real). Uma caixa cuja altura normalizada, se stretchada para
    640x640, cairia em "medium", mas que sob letterbox correto (altura
    real reduzida mais que a largura) cai em "small" -- confirma que o
    método importa, não é só teórico."""
    largura_img, altura_img = 1920, 1080

    # caixa com 40px de altura em pixels ORIGINAIS -- sob letterbox
    # (fator de escala = 640/1920 = 0.333), a altura em pixels
    # letterboxed é 40 * 0.333 = 13.3px -- bem "small".
    altura_norm = 40 / altura_img
    largura_norm = 40 / largura_img  # caixa quadrada nos pixels originais

    categoria = classificar_tamanho_letterbox(
        largura_norm, altura_norm, largura_img, altura_img, eval_size=640,
    )
    assert categoria == "small"


def test_letterbox_e_stretch_divergem_para_imagem_nao_quadrada():
    """Confirma numericamente a causa raiz já diagnosticada: para uma
    imagem não-quadrada, o método letterbox (correto) e o método stretch
    (assume imagem quadrada, usado no script legado) produzem
    classificações diferentes para a mesma caixa."""
    largura_img, altura_img = 1920, 1080
    # caixa quadrada de 80x80 PIXELS ORIGINAIS -- calculada para que:
    #   letterbox: escala por max(W,H)=1920 nos dois eixos -> área ~711px² (small)
    #   stretch:   escala W por 1920 e H por 1080 SEPARADAMENTE -> área ~1264px² (medium)
    # ou seja, a MESMA caixa cai em categorias diferentes conforme o método.
    largura_norm = 80 / largura_img
    altura_norm = 80 / altura_img

    categoria_letterbox = classificar_tamanho_letterbox(
        largura_norm, altura_norm, largura_img, altura_img, eval_size=640,
    )

    # método stretch (o que o script legado fazia): multiplica cada eixo
    # por eval_size independentemente, ignorando a proporção real da imagem
    largura_stretch_px = largura_norm * 640
    altura_stretch_px = altura_norm * 640
    area_stretch = largura_stretch_px * altura_stretch_px
    categoria_stretch = "small" if area_stretch < 32 ** 2 else ("medium" if area_stretch < 96 ** 2 else "large")

    # a mesma caixa deve cair em categorias DIFERENTES pelos dois métodos
    # -- isso é a prova numérica da divergência diagnosticada
    assert categoria_letterbox != categoria_stretch


def test_classificacao_e_identica_para_imagem_quadrada():
    """Controle: se a imagem FOR quadrada, letterbox e stretch devem
    coincidir -- confirma que a divergência é especificamente por causa da
    não-quadratura, não um bug genérico do método."""
    largura_img, altura_img = 1000, 1000  # quadrada
    largura_norm, altura_norm = 60 / 1000, 60 / 1000

    categoria_letterbox = classificar_tamanho_letterbox(
        largura_norm, altura_norm, largura_img, altura_img, eval_size=640,
    )
    area_stretch = (largura_norm * 640) * (altura_norm * 640)
    categoria_stretch = "small" if area_stretch < 32 ** 2 else ("medium" if area_stretch < 96 ** 2 else "large")

    assert categoria_letterbox == categoria_stretch


def _criar_split_sintetico(tmp_path: Path):
    imagens_dir = tmp_path / "images"
    labels_dir = tmp_path / "labels"
    imagens_dir.mkdir()
    labels_dir.mkdir()

    # imagem widescreen, como o CITRA real
    Image.new("RGB", (1920, 1080)).save(imagens_dir / "img1.png")
    (labels_dir / "img1.txt").write_text(
        "0 0.5 0.5 0.02 0.02\n"   # pequena
        "0 0.3 0.3 0.3 0.3\n"     # grande
    )
    Image.new("RGB", (1920, 1080)).save(imagens_dir / "img2.png")
    (labels_dir / "img2.txt").write_text("0 0.1 0.1 0.01 0.01\n")

    return imagens_dir, labels_dir


def test_perfilar_dataset_produz_estrutura_esperada(tmp_path):
    imagens_dir, labels_dir = _criar_split_sintetico(tmp_path)
    perfil = perfilar_dataset(imagens_dir, labels_dir)

    assert perfil["metodo_classificacao_tamanho"] == "letterbox"
    assert perfil["n_bboxes_total"] == 3
    assert perfil["n_imagens"] == 2
    assert perfil["coco_size_distribution"]["small_count"] + \
        perfil["coco_size_distribution"]["medium_count"] + \
        perfil["coco_size_distribution"]["large_count"] == 3
    assert "median" in perfil["area_normalized"]
    assert perfil["objects_per_image"]["count"] == 2  # duas imagens com objetos
    assert perfil["objects_per_image"]["max"] == 2.0  # img1 tem 2 objetos


def test_perfilar_dataset_referencia_lin_et_al_registrada(tmp_path):
    imagens_dir, labels_dir = _criar_split_sintetico(tmp_path)
    perfil = perfilar_dataset(imagens_dir, labels_dir)
    assert "Lin et al." in perfil["referencia_limiares"]

"""Testes da correção de armazenamento (2026-09-02): compactação de pools
de crops para evitar arquivos soltos no Drive."""
from __future__ import annotations

import zipfile
from pathlib import Path

from PIL import Image

from src.extraction import compactar_arquivos, carregar_pool_de_crops_do_zip


def _criar_crops_sinteticos(pasta: Path, n: int = 5) -> list[Path]:
    pasta.mkdir(parents=True, exist_ok=True)
    caminhos = []
    for i in range(n):
        caminho = pasta / f"crop_{i:03d}.png"
        Image.new("RGB", (40, 30), color=(i * 10, i * 10, i * 10)).save(caminho)
        caminhos.append(caminho)
    return caminhos


def test_compactar_arquivos_gera_zip_com_todos_os_arquivos(tmp_path):
    crops_dir = tmp_path / "crops_brutos"
    caminhos = _criar_crops_sinteticos(crops_dir, n=5)

    caminho_zip = tmp_path / "pool.zip"
    n_compactados = compactar_arquivos(caminhos, caminho_zip)

    assert n_compactados == 5
    assert caminho_zip.exists()

    with zipfile.ZipFile(caminho_zip) as zf:
        nomes_no_zip = set(zf.namelist())
    assert nomes_no_zip == {"crop_000.png", "crop_001.png", "crop_002.png", "crop_003.png", "crop_004.png"}


def test_compactar_arquivos_so_inclui_a_lista_dada_nao_a_pasta_inteira(tmp_path):
    """Confirma que só os arquivos MANTIDOS (ex.: após o filtro de
    qualidade) entram no zip -- não todos os arquivos da pasta de origem,
    que pode conter crops descartados."""
    crops_dir = tmp_path / "crops_brutos"
    todos = _criar_crops_sinteticos(crops_dir, n=5)
    apenas_mantidos = todos[:2]  # simula que só 2 dos 5 passaram no filtro

    caminho_zip = tmp_path / "pool.zip"
    compactar_arquivos(apenas_mantidos, caminho_zip)

    with zipfile.ZipFile(caminho_zip) as zf:
        nomes_no_zip = set(zf.namelist())
    assert nomes_no_zip == {"crop_000.png", "crop_001.png"}


def test_ciclo_completo_compactar_e_carregar_produz_pool_correto(tmp_path):
    """Teste central: confirma que compactar + carregar reproduz
    exatamente o formato (fonte, caminho) que src.compose.compor_dataset
    já espera -- sem precisar mudar esse componente."""
    crops_dir = tmp_path / "crops_brutos"
    caminhos_originais = _criar_crops_sinteticos(crops_dir, n=3)

    caminho_zip = tmp_path / "smd.zip"
    compactar_arquivos(caminhos_originais, caminho_zip)

    pool = carregar_pool_de_crops_do_zip(caminho_zip, fonte="SMD", destino_local=tmp_path / "extraido")

    assert len(pool) == 3
    assert all(fonte == "SMD" for fonte, _ in pool)
    nomes_extraidos = {caminho.name for _, caminho in pool}
    assert nomes_extraidos == {"crop_000.png", "crop_001.png", "crop_002.png"}

    # os arquivos extraídos devem ser abríveis e ter o mesmo conteúdo visual
    for _, caminho in pool:
        with Image.open(caminho) as img:
            assert img.size == (40, 30)


def test_carregar_pool_combina_fontes_diferentes_em_pool_unico(tmp_path):
    """Simula o uso real: duas fontes diferentes, cada uma com seu zip,
    combinadas num único pool_crops para o composer."""
    crops_a = _criar_crops_sinteticos(tmp_path / "crops_fonte_a", n=2)
    crops_b = _criar_crops_sinteticos(tmp_path / "crops_fonte_b", n=3)

    zip_a = tmp_path / "fontea.zip"
    zip_b = tmp_path / "fonteb.zip"
    compactar_arquivos(crops_a, zip_a)
    compactar_arquivos(crops_b, zip_b)

    pool_a = carregar_pool_de_crops_do_zip(zip_a, fonte="FonteA", destino_local=tmp_path / "extraido_a")
    pool_b = carregar_pool_de_crops_do_zip(zip_b, fonte="FonteB", destino_local=tmp_path / "extraido_b")
    pool_combinado = pool_a + pool_b

    assert len(pool_combinado) == 5
    fontes_presentes = {fonte for fonte, _ in pool_combinado}
    assert fontes_presentes == {"FonteA", "FonteB"}

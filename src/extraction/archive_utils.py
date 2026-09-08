"""
Compactação de pools de crops para armazenamento no Drive (correção do
problema de I/O via FUSE, ver docs/CHANGELOG_metodologico.md, 2026-09-02).

Achado que motiva este módulo: copiar dezenas de milhares de arquivos
individuais para o Google Drive montado via FUSE no Colab causa
instabilidade (`OSError: Input/output error`), não apenas deixa os
arquivos vulneráveis depois de salvos -- a própria operação de copiar
muitos arquivos pequenos, um a um, é o que estressa o FUSE. A correção:
compactar LOCALMENTE (rápido, sistema de arquivos local do Colab) e copiar
um ÚNICO arquivo `.zip` para o Drive (uma operação de escrita, não
milhares) -- consistente com a convenção já registrada em
docs/README_DRIVE.md (§12.1 do plano): "um .zip por artefato pesado, não
pastas soltas com muitos arquivos pequenos".

Este módulo NÃO modifica src/compose/compose.py -- a extração de volta
para arquivos soltos (`carregar_pool_de_crops_do_zip`) acontece antes de
chamar `compor_dataset`, que continua recebendo `pool_crops` no mesmo
formato de sempre: list[(fonte, caminho_do_arquivo)].
"""
from __future__ import annotations

import zipfile
from pathlib import Path


def compactar_arquivos(caminhos: list[Path], caminho_zip_destino: Path) -> int:
    """Compacta uma lista específica de arquivos (não uma pasta inteira --
    importa quando só um subconjunto dos arquivos de uma pasta deve entrar,
    ex.: só os crops que passaram no filtro de qualidade) num único .zip.

    Retorna o número de arquivos compactados.
    """
    caminho_zip_destino = Path(caminho_zip_destino)
    caminho_zip_destino.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(caminho_zip_destino, "w", zipfile.ZIP_DEFLATED) as zf:
        for caminho in caminhos:
            zf.write(caminho, arcname=Path(caminho).name)

    return len(caminhos)


def carregar_pool_de_crops_do_zip(
    caminho_zip: Path, fonte: str, destino_local: Path,
) -> list[tuple[str, Path]]:
    """Extrai um .zip de pool de crops (gerado por compactar_arquivos) para
    uma pasta local, e retorna a lista pronta no formato que
    src.compose.compor_dataset espera: list[(fonte, caminho)].

    Uso típico: antes de rodar a composição sintética, extrair o(s) zip(s)
    de cada fonte para pastas locais temporárias, montar o pool_crops
    combinado, e só então chamar compor_dataset -- sem nenhuma mudança no
    componente de composição em si.
    """
    caminho_zip = Path(caminho_zip)
    destino_local = Path(destino_local)
    destino_local.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(caminho_zip) as zf:
        zf.extractall(destino_local)

    return [(fonte, p) for p in sorted(destino_local.iterdir()) if p.is_file()]

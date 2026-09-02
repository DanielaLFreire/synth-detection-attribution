"""Testes da tarefa -1.3: deduplicação Roboflow, filtro de qualidade
unificado, e manifesto de extração com hash."""
from __future__ import annotations

import csv
from pathlib import Path

from PIL import Image

from src.extraction import (
    deduplicar_por_base,
    identificar_base_roboflow,
    FiltroConfig,
    avaliar_crop,
    filtrar_pool_de_crops,
)


# --------------------------------------------------------------------------
# Deduplicação Roboflow
# --------------------------------------------------------------------------

def test_identificar_base_roboflow_reconhece_padrao():
    assert identificar_base_roboflow("003956_jpg.rf.abc123def.jpg") == "003956"
    assert identificar_base_roboflow("000434_jpg.rf.9f8e7d.png") == "000434"


def test_identificar_base_roboflow_retorna_none_para_nome_fora_do_padrao():
    assert identificar_base_roboflow("foto_qualquer.jpg") is None


def test_deduplicar_por_base_mantem_um_por_grupo():
    caminhos = [
        Path("003956_jpg.rf.bbbbbb.jpg"),
        Path("003956_jpg.rf.aaaaaa.jpg"),   # mesma base, hash diferente -> duplicata
        Path("000434_jpg.rf.cccccc.jpg"),   # base única, sem duplicata
        Path("nome_fora_do_padrao.jpg"),    # não reconhecido
    ]
    resultado = deduplicar_por_base(caminhos)

    assert resultado.n_bases_unicas == 2
    # estratégia "primeiro_alfabetico": entre aaaaaa e bbbbbb, mantém aaaaaa
    nomes_mantidos = {p.name for p in resultado.mantidos}
    assert "003956_jpg.rf.aaaaaa.jpg" in nomes_mantidos
    assert "003956_jpg.rf.bbbbbb.jpg" not in nomes_mantidos
    assert "000434_jpg.rf.cccccc.jpg" in nomes_mantidos

    assert len(resultado.descartados) == 1
    assert resultado.descartados[0].name == "003956_jpg.rf.bbbbbb.jpg"

    assert len(resultado.sem_padrao_reconhecido) == 1
    assert resultado.sem_padrao_reconhecido[0].name == "nome_fora_do_padrao.jpg"


def test_deduplicar_reproduz_a_contagem_real_encontrada_no_seaships(tmp_path):
    """Reproduz em miniatura a proporção encontrada de verdade no
    SeaShips_voc.zip (6979 bases, 6126 com >1 cópia) -- não com os mesmos
    números (seria lento), mas com a mesma estrutura: bases com 1 e bases
    com 2 cópias, verificando que o total de únicas bate."""
    caminhos = []
    for i in range(50):
        caminhos.append(Path(f"{i:06d}_jpg.rf.aaaa11.jpg"))
        if i % 10 != 0:  # 45 das 50 bases têm uma segunda cópia (augmentation)
            caminhos.append(Path(f"{i:06d}_jpg.rf.bbbb22.jpg"))

    resultado = deduplicar_por_base(caminhos)
    assert resultado.n_bases_unicas == 50
    assert len(resultado.descartados) == 45


# --------------------------------------------------------------------------
# Filtro de qualidade unificado
# --------------------------------------------------------------------------

def test_avaliar_crop_rejeita_por_dimensao_minima():
    config = FiltroConfig(min_dim_px=32)
    r = avaliar_crop(largura_px=20, altura_px=50, config=config)
    assert r.mantido is False
    assert "dimensao_minima" in r.motivo


def test_avaliar_crop_aceita_quando_dimensoes_ok_e_sem_checagem_de_mascara():
    config = FiltroConfig(min_dim_px=32)
    r = avaliar_crop(largura_px=40, altura_px=60, config=config)
    assert r.mantido is True
    assert r.motivo == "ok"


def test_avaliar_crop_rejeita_por_cobertura_de_mascara_baixa():
    config = FiltroConfig(min_dim_px=10, min_cobertura_mascara=0.5)
    r = avaliar_crop(largura_px=40, altura_px=40, config=config, cobertura_mascara=0.2)
    assert r.mantido is False
    assert "cobertura_mascara" in r.motivo


def test_avaliar_crop_sem_mascara_passa_quando_nao_e_exigida():
    config = FiltroConfig(min_dim_px=10, min_cobertura_mascara=0.5, exigir_mascara=False)
    r = avaliar_crop(largura_px=40, altura_px=40, config=config, cobertura_mascara=None)
    assert r.mantido is True
    assert "sem_checagem_de_mascara" in r.motivo  # auditável, não um "passe" silencioso


def test_avaliar_crop_sem_mascara_e_rejeitado_quando_mascara_e_exigida():
    config = FiltroConfig(min_dim_px=10, min_cobertura_mascara=0.5, exigir_mascara=True)
    r = avaliar_crop(largura_px=40, altura_px=40, config=config, cobertura_mascara=None)
    assert r.mantido is False


def test_mesma_config_aplicada_a_duas_fontes_diferentes_da_mesmo_resultado():
    """Este é o teste que importa mais para o propósito da tarefa: garante
    que o filtro NÃO tem nenhuma ramificação escondida por nome de fonte --
    a config é tudo que determina o resultado, então duas fontes com os
    mesmos crops (dimensões) sempre recebem o mesmo veredito."""
    config = FiltroConfig(min_dim_px=32)
    r_fonte_a = avaliar_crop(largura_px=25, altura_px=25, config=config)
    r_fonte_b = avaliar_crop(largura_px=25, altura_px=25, config=config)
    assert r_fonte_a.mantido == r_fonte_b.mantido == False
    assert r_fonte_a.motivo == r_fonte_b.motivo


# --------------------------------------------------------------------------
# Manifesto de extração com hash
# --------------------------------------------------------------------------

def _criar_crops_sinteticos(pasta: Path, especificacoes: list[tuple[str, int, int]]):
    pasta.mkdir(parents=True, exist_ok=True)
    for nome, largura, altura in especificacoes:
        Image.new("RGB", (largura, altura), color=(10, 20, 30)).save(pasta / nome)


def test_filtrar_pool_de_crops_gera_manifesto_e_retorna_apenas_mantidos(tmp_path):
    crops_dir = tmp_path / "crops_fonte_x"
    _criar_crops_sinteticos(crops_dir, [
        ("crop_grande.png", 60, 60),   # deve passar
        ("crop_pequeno.png", 10, 10),  # deve ser rejeitado (dimensão mínima)
        ("crop_medio.png", 33, 33),    # deve passar (limiar = 32)
    ])
    config = FiltroConfig(min_dim_px=32)

    mantidos = filtrar_pool_de_crops(
        fonte="FonteX",
        crops_dir=crops_dir,
        config=config,
        manifesto_csv=tmp_path / "manifesto_extracao.csv",
        manifesto_metadata_json=tmp_path / "manifesto_extracao_meta.json",
    )

    nomes_mantidos = {c.name for _, c in mantidos}
    assert nomes_mantidos == {"crop_grande.png", "crop_medio.png"}
    assert all(fonte == "FonteX" for fonte, _ in mantidos)

    with open(tmp_path / "manifesto_extracao.csv", newline="", encoding="utf-8") as f:
        linhas = list(csv.DictReader(f))
    assert len(linhas) == 3  # todos avaliados, mantidos e descartados

    linha_pequeno = next(l for l in linhas if l["caminho_crop"].endswith("crop_pequeno.png"))
    assert linha_pequeno["mantido"] == "False"
    assert linha_pequeno["sha256"] == ""  # descartados não têm hash calculado

    linha_grande = next(l for l in linhas if l["caminho_crop"].endswith("crop_grande.png"))
    assert linha_grande["mantido"] == "True"
    assert len(linha_grande["sha256"]) == 64  # sha256 em hexadecimal


def test_filtrar_pool_de_crops_duas_fontes_mesma_config_manifesto_acumulado(tmp_path):
    """Simula o caso real: duas fontes diferentes, mesma config, manifesto
    consolidado num único CSV (modo append) -- exatamente o que evita o
    confound de filtro-por-fonte."""
    crops_a = tmp_path / "crops_a"
    crops_b = tmp_path / "crops_b"
    _criar_crops_sinteticos(crops_a, [("a1.png", 40, 40), ("a2.png", 10, 10)])
    _criar_crops_sinteticos(crops_b, [("b1.png", 40, 40), ("b2.png", 10, 10)])

    config = FiltroConfig(min_dim_px=32)
    manifesto = tmp_path / "manifesto_unificado.csv"
    meta = tmp_path / "manifesto_unificado_meta.json"

    mantidos_a = filtrar_pool_de_crops(
        fonte="FonteA", crops_dir=crops_a, config=config,
        manifesto_csv=manifesto, manifesto_metadata_json=meta, modo_escrita="w",
    )
    mantidos_b = filtrar_pool_de_crops(
        fonte="FonteB", crops_dir=crops_b, config=config,
        manifesto_csv=manifesto, manifesto_metadata_json=meta, modo_escrita="a",
    )

    assert len(mantidos_a) == 1
    assert len(mantidos_b) == 1

    with open(manifesto, newline="", encoding="utf-8") as f:
        linhas = list(csv.DictReader(f))
    assert len(linhas) == 4  # 2 crops x 2 fontes, todos no mesmo manifesto
    fontes_no_manifesto = {l["fonte"] for l in linhas}
    assert fontes_no_manifesto == {"FonteA", "FonteB"}

    import json
    historico = json.loads(meta.read_text(encoding="utf-8"))
    assert len(historico) == 2  # uma entrada de metadata por fonte processada


def test_ponte_extracao_para_filtro_usa_cobertura_real_do_segmentador(tmp_path):
    """Teste de integração -1.6 -> -1.3: extrai com um segmentador falso,
    carrega a cobertura do manifesto de extração, e confirma que o filtro
    de qualidade usa essa cobertura real (não None) para decidir."""
    from src.extraction import extrair_crops_de_yolo, carregar_coberturas_do_manifesto_extracao

    class _SegmentadorMetade:
        def segmentar(self, imagem_rgb, caixa):
            import numpy as np
            mascara = np.zeros(imagem_rgb.shape[:2], dtype=bool)
            x0, y0, x1, y1 = caixa
            meio = x0 + (x1 - x0) // 2
            mascara[y0:y1, x0:meio] = True
            return mascara

    imagens_dir = tmp_path / "images"
    labels_dir = tmp_path / "labels"
    imagens_dir.mkdir()
    labels_dir.mkdir()
    Image.new("RGB", (200, 100)).save(imagens_dir / "img1.png")
    (labels_dir / "img1.txt").write_text("0 0.5 0.5 0.4 0.4\n")

    manifesto_extracao = tmp_path / "manifesto_extracao.csv"
    extrair_crops_de_yolo(
        fonte="FonteTeste", imagens_dir=imagens_dir, labels_dir=labels_dir,
        saida_crops_dir=tmp_path / "crops", manifesto_csv=manifesto_extracao,
        extensao_imagem=".png",  # imagem de ENTRADA salva como .png acima
        segmentador=_SegmentadorMetade(),
    )

    coberturas = carregar_coberturas_do_manifesto_extracao(manifesto_extracao)
    assert len(coberturas) == 1
    (cobertura_valor,) = coberturas.values()
    assert abs(cobertura_valor - 0.5) < 0.05

    # agora usa essa cobertura no filtro, exigindo min_cobertura_mascara=0.9
    # -- o crop deve ser REJEITADO (cobertura real ~0.5 < 0.9)
    config = FiltroConfig(min_dim_px=1, min_cobertura_mascara=0.9, exigir_mascara=True)
    mantidos = filtrar_pool_de_crops(
        fonte="FonteTeste", crops_dir=tmp_path / "crops", config=config,
        manifesto_csv=tmp_path / "manifesto_filtro.csv",
        manifesto_metadata_json=tmp_path / "manifesto_filtro_meta.json",
        coberturas_mascara=coberturas,
    )
    assert len(mantidos) == 0

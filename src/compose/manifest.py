"""
Schema e escrita do manifesto de composição por colagem.

Cada linha deste manifesto descreve UMA colagem (um crop colado numa caixa
de destino, numa variação específica de uma imagem-alvo). Sem este manifesto,
as features da Família 2 (transformação: fator_reescala, upsample, etc.) do
Estágio A não são reconstituíveis — ver §5.3 do plano de pré-registro.

Referências metodológicas para a técnica de composição implementada aqui:
- Dwibedi, D., Misra, I., Hebert, M. (2017). "Cut, Paste and Learn:
  Surprisingly Easy Synthesis for Instance Detection." ICCV 2017.
- Ghiasi, G. et al. (2021). "Simple Copy-Paste is a Strong Data Augmentation
  Method for Instance Segmentation." CVPR 2021.
Ver docs/referencias_metodologicas.md para a citação completa.
"""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass, fields, asdict
from datetime import datetime, timezone
from pathlib import Path

MANIFEST_VERSION = "1.0"


@dataclass
class ManifestRow:
    """Uma linha do manifesto = uma colagem.

    O campo `grupo_geometrico_id` é a chave de agrupamento exigida em §5.1
    do plano: todas as colagens que compartilham a mesma (imagem, caixa)
    têm o MESMO grupo_geometrico_id, porque a geometria (posição, área da
    caixa de destino) é herdada e idêntica entre variações -- qualquer
    modelo estatístico que consuma este manifesto deve fazer validação
    cruzada por grupo, nunca por linha individual, para features espaciais.
    """

    # --- identificação e proveniência ---
    manifest_version: str
    run_id: str                 # um id por execução do compose (auditoria completa)
    timestamp_geracao: str      # ISO 8601, UTC

    # --- localização da colagem no dataset-alvo ---
    split: str                  # "train" | "val" | "test" -- ver bloqueio de treino
    imagem_id: str              # stem do arquivo de imagem-alvo (ex.: "18.04.2022-15-56-19")
    box_index: int              # índice da caixa dentro do label original daquela imagem
    grupo_geometrico_id: str    # f"{imagem_id}__{box_index}" -- chave de agrupamento (§5.1)
    variacao_k: int             # qual das n_variations esta colagem representa

    # --- geometria da caixa de destino (herdada do label real, nunca sorteada) ---
    caixa_x0_px: int
    caixa_y0_px: int
    caixa_x1_px: int
    caixa_y1_px: int
    caixa_largura_px: int
    caixa_altura_px: int
    imagem_largura_px: int
    imagem_altura_px: int

    # --- proveniência do crop colado ---
    fonte: str                       # nome da fonte pública (ex.: "ABOShips")
    crop_path: str                   # caminho relativo do arquivo de crop usado
    crop_largura_original_px: int
    crop_altura_original_px: int

    # --- transformação aplicada (Família 2 -- tratamento, não pré-processamento) ---
    fator_reescala: float            # área_destino / área_original_do_crop
    upsample: bool                   # fator_reescala > 1
    metodo_interpolacao: str         # constante e documentada -- ver compose.py

    # --- reprodutibilidade desta colagem específica ---
    seed_sorteio: int                # seed/índice de sorteio usado para ESTA colagem

    # --- saída gerada ---
    imagem_destino_path: str
    label_destino_path: str


MANIFEST_FIELDNAMES = [f.name for f in fields(ManifestRow)]


class ManifestWriter:
    """Escritor incremental de manifesto em CSV.

    CSV (não Parquet) por simplicidade e ausência de dependência extra nesta
    primeira versão -- §12.1 do plano aceita CSV ou Parquet. Uma conversão
    para Parquet pode ser adicionada depois sem mudar o schema, se o volume
    justificar.
    """

    def __init__(self, caminho_csv: Path):
        self.caminho_csv = Path(caminho_csv)
        self.caminho_csv.parent.mkdir(parents=True, exist_ok=True)
        self._arquivo = open(self.caminho_csv, "w", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(self._arquivo, fieldnames=MANIFEST_FIELDNAMES)
        self._writer.writeheader()
        self._n_linhas = 0

    def escrever(self, linha: ManifestRow) -> None:
        self._writer.writerow(asdict(linha))
        self._n_linhas += 1

    def fechar(self) -> int:
        self._arquivo.close()
        return self._n_linhas

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.fechar()


def escrever_metadata_execucao(caminho_json: Path, config: dict, n_linhas: int,
                                inicio: datetime, fim: datetime) -> None:
    """Grava metadado de nível de execução (não por colagem) ao lado do
    manifesto: parâmetros usados, contagem total, duração. Este arquivo é o
    que permite auditar DEPOIS com que configuração um manifesto foi gerado,
    sem precisar reconstruir isso de memória."""
    caminho_json = Path(caminho_json)
    caminho_json.parent.mkdir(parents=True, exist_ok=True)
    metadata = {
        "manifest_version": MANIFEST_VERSION,
        "config": config,
        "n_linhas_geradas": n_linhas,
        "inicio_utc": inicio.isoformat(),
        "fim_utc": fim.isoformat(),
        "duracao_segundos": (fim - inicio).total_seconds(),
    }
    with open(caminho_json, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)


def novo_run_id() -> str:
    """Um id de execução legível e ordenável por tempo (não é um hash --
    propositalmente simples, para que dois humanos consigam comparar
    execuções olhando o nome)."""
    return datetime.now(timezone.utc).strftime("run_%Y%m%dT%H%M%SZ")

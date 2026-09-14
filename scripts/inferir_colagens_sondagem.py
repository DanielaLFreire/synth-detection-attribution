"""
Script de entrada para a Fase 2 (Estágio A) -- a ÚNICA etapa de GPU desta
fase: roda os 3 checkpoints de B2 (seeds 42, 123, 2024, `weights/last.pt`
= época 150, coerente com epoca_checkpoint=150 fechado na Fase 1) sobre
as 6.640 imagens de sondagem geradas na tarefa 0.4, salvando TODAS as
detecções brutas (limiar de confiança mínimo) no Drive.

Desenho para gastar GPU uma única vez: qualquer decisão posterior (limiar
de confiança, critério de IoU, forma de votação entre seeds) é feita em
CPU sobre as detecções salvas -- nunca voltando à GPU.

Por que B2 e não A_joint como gerador do alvo: B2 foi treinado só com
dados reais, nunca viu uma colagem -- seu "acerto" mede realismo/
plausibilidade da composição sem circularidade. A_joint foi treinado
nesse mesmo estilo de colagem e acertaria por familiaridade com o
estilo, não por qualidade (risco de circularidade já registrado no
plano, §5.6). Decisão confirmada em 2026-09-14.

Uso no Colab (GPU necessária):

    import sys
    sys.path.insert(0, "/content/synth-detection-attribution")
    from scripts.inferir_colagens_sondagem import main

    main()
"""
from __future__ import annotations

import csv
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

DRIVE_SONDAGEM = "/content/drive/MyDrive/PROJETO_MARINHA/EXPERIMENTO_ATRIBUICAO_CAUSAL/estagio_a/colagens_sondagem_val"
DRIVE_RUNS = "/content/drive/MyDrive/PROJETO_MARINHA/EXPERIMENTO_ATRIBUICAO_CAUSAL/fase1_piloto/runs"
DRIVE_DETECCOES = "/content/drive/MyDrive/PROJETO_MARINHA/EXPERIMENTO_ATRIBUICAO_CAUSAL/estagio_a/deteccoes_brutas"

SEEDS_B2 = [42, 123, 2024]
CONF_MINIMO = 0.001   # mínimo -- salvamos tudo, decidimos o limiar depois em CPU
IMGSZ = 640           # mesmo tamanho usado no treino (protocolo V2)


def main(
    destino_local: str = "/content/estagio_a_local",
    drive_sondagem: str = DRIVE_SONDAGEM,
    drive_runs: str = DRIVE_RUNS,
    drive_deteccoes: str = DRIVE_DETECCOES,
    seeds: list[int] | None = None,
    conf_minimo: float = CONF_MINIMO,
    imgsz: int = IMGSZ,
) -> dict:
    from ultralytics import YOLO  # import tardio -- GPU

    seeds = seeds or SEEDS_B2
    destino_local = Path(destino_local)
    drive_deteccoes = Path(drive_deteccoes)
    drive_deteccoes.mkdir(parents=True, exist_ok=True)

    print("1) Extraindo as imagens de sondagem para disco local...")
    imagens_dir = destino_local / "colagens" / "images"
    imagens_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(Path(drive_sondagem) / "colagens_images.zip") as z:
        z.extractall(imagens_dir)
    imagens = sorted(imagens_dir.glob("*.png"))
    print(f"   {len(imagens)} imagens de sondagem extraídas.\n")

    resumo = {}
    for seed in seeds:
        caminho_pesos = Path(drive_runs) / f"B2_seed{seed}" / "weights" / "last.pt"
        if not caminho_pesos.exists():
            raise FileNotFoundError(f"checkpoint não encontrado: {caminho_pesos}")

        print(f"2) Inferência com B2_seed{seed} (last.pt, época 150) -- conf>={conf_minimo}, imgsz={imgsz}...")
        model = YOLO(str(caminho_pesos))

        caminho_csv = drive_deteccoes / f"deteccoes_B2_seed{seed}.csv"
        n_deteccoes = 0
        n_imagens_processadas = 0
        inicio = datetime.now(timezone.utc)

        with open(caminho_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["seed_checkpoint", "cena_stem", "x0_px", "y0_px", "x1_px", "y1_px", "conf", "classe"])

            # stream=True: processa uma imagem por vez, sem acumular tudo na memória
            for resultado in model.predict(
                source=str(imagens_dir), conf=conf_minimo, imgsz=imgsz,
                stream=True, verbose=False,
            ):
                cena_stem = Path(resultado.path).stem
                n_imagens_processadas += 1
                if resultado.boxes is None or len(resultado.boxes) == 0:
                    continue
                caixas = resultado.boxes.xyxy.cpu().numpy()
                confs = resultado.boxes.conf.cpu().numpy()
                classes = resultado.boxes.cls.cpu().numpy()
                for (x0, y0, x1, y1), conf, cls in zip(caixas, confs, classes):
                    writer.writerow([seed, cena_stem, f"{x0:.1f}", f"{y0:.1f}", f"{x1:.1f}", f"{y1:.1f}",
                                     f"{conf:.5f}", int(cls)])
                    n_deteccoes += 1

        fim = datetime.now(timezone.utc)
        print(f"   {n_imagens_processadas} imagens processadas, {n_deteccoes} detecções salvas "
              f"em {caminho_csv.name} ({(fim - inicio).total_seconds():.0f}s)\n")
        resumo[f"B2_seed{seed}"] = {
            "checkpoint": str(caminho_pesos),
            "n_imagens": n_imagens_processadas,
            "n_deteccoes": n_deteccoes,
            "segundos": (fim - inicio).total_seconds(),
        }

    metadata = {
        "gerado_em_utc": datetime.now(timezone.utc).isoformat(),
        "conf_minimo": conf_minimo,
        "imgsz": imgsz,
        "checkpoint_usado": "weights/last.pt (época 150, epoca_checkpoint fechado na Fase 1)",
        "braco_gerador_do_alvo": "B2 (treinado só com real -- sem circularidade)",
        "n_imagens_sondagem": len(imagens),
        "por_checkpoint": resumo,
    }
    (drive_deteccoes / "metadata_inferencia.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8",
    )

    print(f"✅ Concluído. Detecções brutas dos {len(seeds)} checkpoints salvas em {drive_deteccoes}")
    print("   A partir daqui, tudo é CPU -- a GPU não é mais necessária nesta fase.")
    return metadata


if __name__ == "__main__":
    main()

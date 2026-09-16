"""
Fase 4 -- verificações ANTES da avaliação única do teste. Nenhum modelo é
carregado, nenhuma predição é feita: só estrutura, perfil e ISOLAMENTO.

Checagens (todas devem passar para GO):
 1. test/images e test/labels_final existem; imagens e labels pareados.
 2. Perfil das caixas (n, fração small a 640) -- comparável a val/Fase 0.
 3. Isolamento por NOME: stems do teste ∩ {train, val} = ∅.
 4. Isolamento por CONTEÚDO: hash md5 das imagens do teste ∩ {train, val} = ∅
    (detecta a mesma imagem com outro nome).
 5. Isolamento contra tudo que geramos: stems do teste ∩ {manifesto de
    sondagem (Estágio A), manifesto de sintéticas de treino (Fase 1),
    manifestos das 4 células (Fase 3), caixas_viaveis_fase3} = ∅.
 6. Os 18 `last.pt` existem no Drive (não avalia nada).
 7. Marcador `fase4/teste_avaliado.json` NÃO existe.

Uso no Colab (CPU basta):

    import sys
    sys.path.insert(0, "/content/synth-detection-attribution")
    from scripts.verificar_teste_fase4 import main
    main()
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

from src.compose.compose import ler_caixas_yolo
from src.evaluation import (stems_imagens, hashes_imagens, pareamento_imagens_labels,
                            stems_em_manifesto, verificar_disjuncao)
from src.factorial import area_letterbox_640

RAIZ = "/content/drive/MyDrive/PROJETO_MARINHA/EXPERIMENTO_ATRIBUICAO_CAUSAL"
CITRA = "/content/drive/MyDrive/PROJETO_MARINHA/Datasets/CITRA-3D-Real"
MANIFESTOS = {
    "sondagem_estagio_a": f"{RAIZ}/estagio_a/colagens_sondagem_val/manifesto_colagens_sondagem_val.csv",
    "sinteticas_treino_fase1": f"{RAIZ}/fase1_piloto/sinteticas_treino/manifesto_sinteticas_treino.csv",
    "celula_casada__alto": f"{RAIZ}/fase3/celulas/manifesto_casada__alto.csv",
    "celula_casada__baixo": f"{RAIZ}/fase3/celulas/manifesto_casada__baixo.csv",
    "celula_reduzida__alto": f"{RAIZ}/fase3/celulas/manifesto_reduzida__alto.csv",
    "celula_reduzida__baixo": f"{RAIZ}/fase3/celulas/manifesto_reduzida__baixo.csv",
    "caixas_viaveis_fase3": "configs/caixas_viaveis_fase3.csv",
}
MODELOS = [f"{RAIZ}/fase3/runs/{b}_seed{s}/weights/last.pt"
           for s in (42, 123, 2024) for b in ("casada__alto", "casada__baixo", "reduzida__alto", "reduzida__baixo", "controle")]
MODELOS += [f"{RAIZ}/fase1_piloto/runs/B2_seed{s}/weights/last.pt" for s in (42, 123, 2024)]
MARCADOR = f"{RAIZ}/fase4/teste_avaliado.json"


def _perfil_caixas(pasta_imgs: Path, pasta_lbls: Path) -> dict:
    n, small = 0, 0
    for label in sorted(pasta_lbls.glob("*.txt")):
        img = next((pasta_imgs / f"{label.stem}{e}" for e in (".jpg", ".jpeg", ".png") if (pasta_imgs / f"{label.stem}{e}").exists()), None)
        if img is None:
            continue
        with Image.open(img) as im:
            W, H = im.size
        for c in ler_caixas_yolo(label, W, H):
            n += 1
            small += area_letterbox_640(float(max(1, c.largura) * max(1, c.altura)), W, H) < 32 * 32
    return {"n_caixas": n, "fracao_small_640": (small / n if n else float("nan"))}


def main(citra: str = CITRA) -> bool:
    citra = Path(citra)
    ok = True
    def chk(cond: bool, msg: str):
        nonlocal ok
        print(f"  {'✅' if cond else '❌'} {msg}")
        ok &= bool(cond)

    print("1) Estrutura do split de teste")
    t_img, t_lbl = citra / "test" / "images", citra / "test" / "labels_final"
    chk(t_img.is_dir(), f"pasta {t_img}"); chk(t_lbl.is_dir(), f"pasta {t_lbl}")
    if not (t_img.is_dir() and t_lbl.is_dir()):
        print("\nNO-GO: split de teste não encontrado nos caminhos esperados. Passe main(citra=...) com o caminho certo.")
        return False
    par = pareamento_imagens_labels(t_img, t_lbl)
    chk(par["n_imagens"] > 0, f"{par['n_imagens']} imagens, {par['n_labels']} labels")
    chk(not par["imagens_sem_label"], f"imagens sem label: {len(par['imagens_sem_label'])}")
    chk(not par["labels_sem_imagem"], f"labels sem imagem: {len(par['labels_sem_imagem'])}")

    print("\n2) Perfil das caixas do teste")
    perfil = _perfil_caixas(t_img, t_lbl)
    print(f"  {perfil['n_caixas']} caixas, fração small a 640 = {perfil['fracao_small_640']:.3f}  (val: 0,857; Fase 0: 0,822)")
    chk(perfil["n_caixas"] > 0, "há caixas anotadas")

    print("\n3) Isolamento por NOME (stems) contra train e val")
    s_test = stems_imagens(t_img)
    s_train = stems_imagens(citra / "train" / "images"); s_val = stems_imagens(citra / "val" / "images")
    dj = verificar_disjuncao(s_test, {"train": s_train, "val": s_val})
    for k, v in dj.items():
        chk(not v, f"teste ∩ {k} = {len(v)}" + (f"  ex.: {v[:3]}" if v else ""))

    print("\n4) Isolamento por CONTEÚDO (md5) contra train e val -- pode levar alguns minutos")
    h_test = hashes_imagens(t_img)
    h_train = hashes_imagens(citra / "train" / "images"); h_val = hashes_imagens(citra / "val" / "images")
    for nome, h in (("train", h_train), ("val", h_val)):
        comuns = set(h_test) & set(h)
        chk(not comuns, f"imagens do teste idênticas a {nome}: {len(comuns)}" +
            (f"  ex.: {[(h_test[c], h[c]) for c in list(comuns)[:3]]}" if comuns else ""))
    dup_interno = len(h_test) != len(s_test)
    chk(not dup_interno, f"duplicatas internas no teste: {len(s_test) - len(h_test)}")

    print("\n5) Isolamento contra tudo que o projeto gerou (manifestos)")
    dj2 = verificar_disjuncao(s_test, {k: stems_em_manifesto(Path(v)) for k, v in MANIFESTOS.items()})
    for k, v in dj2.items():
        existe = Path(MANIFESTOS[k]).exists()
        chk(not v, f"teste ∩ {k} = {len(v)}" + ("" if existe else "  (manifesto não encontrado -- checagem vazia)"))

    print("\n6) Modelos no Drive (existência, sem carregar)")
    faltam = [m for m in MODELOS if not Path(m).exists()]
    chk(not faltam, f"{len(MODELOS) - len(faltam)}/{len(MODELOS)} last.pt presentes" + (f"  faltam: {faltam[:2]}..." if faltam else ""))

    print("\n7) Marcador de avaliação única")
    chk(not Path(MARCADOR).exists(), f"marcador ausente ({MARCADOR})")

    print("\n" + ("✅ GO: todas as verificações passaram. Pode rodar avaliar_teste_fase4.main()." if ok
                  else "❌ NO-GO: corrija o que falhou ANTES de avaliar o teste (a avaliação é única)."))
    return ok


if __name__ == "__main__":
    main()

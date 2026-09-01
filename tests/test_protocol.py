"""Testes da tarefa -1.5: protocolo de treino V2 -- warmup em passos
absolutos (não em épocas) e proibição de seleção de checkpoint por val."""
from __future__ import annotations

import pytest

from src.train import (
    ProtocoloTreinoV2,
    ProtocoloInvalido,
    calcular_warmup_epochs_equivalente,
    passos_de_warmup_reais,
    gerar_kwargs_treino,
)


def test_protocolo_exige_epoca_checkpoint_explicita():
    with pytest.raises(ProtocoloInvalido, match="epoca_checkpoint"):
        ProtocoloTreinoV2(pesos_base="yolo11n.pt", epochs_total=300)


def test_protocolo_rejeita_checkpoint_alem_do_total_de_epocas():
    with pytest.raises(ProtocoloInvalido, match="não pode ser maior"):
        ProtocoloTreinoV2(pesos_base="yolo11n.pt", epochs_total=300, epoca_checkpoint=301)


def test_protocolo_rejeita_early_stopping_habilitado():
    with pytest.raises(ProtocoloInvalido, match="early_stopping"):
        ProtocoloTreinoV2(
            pesos_base="yolo11n.pt", epochs_total=300, epoca_checkpoint=250,
            early_stopping_habilitado=True,
        )


def test_protocolo_valido_nao_levanta_erro():
    p = ProtocoloTreinoV2(pesos_base="yolo11n.pt", epochs_total=300, epoca_checkpoint=250)
    assert p.epoca_checkpoint == 250
    assert p.early_stopping_habilitado is False


def test_bug_do_warmup_em_epocas_eh_corrigido():
    """Este é o teste central da tarefa: reproduz em miniatura o bug
    documentado (warmup em épocas produz passos diferentes entre braços de
    tamanhos diferentes) e confirma que warmup_epochs calculado por braço
    produz o MESMO número de passos reais.

    Cenário do bug real: braço baseline (B2) com N imagens/época, braço
    joint com 2N imagens/época (real + sintético). Warmup fixo em "épocas"
    daria o dobro de passos reais de warmup ao braço joint. Aqui,
    calculamos warmup_epochs separadamente para cada um a partir do MESMO
    warmup_steps_alvo, e confirmamos que os passos reais batem.
    """
    warmup_steps_alvo = 500
    batch_size = 16

    n_imagens_baseline = 1348          # ex.: só o treino real do CITRA
    n_imagens_joint = 1348 * 2         # real + sintético, dobro de imagens/época

    warmup_epochs_baseline = calcular_warmup_epochs_equivalente(
        warmup_steps_alvo, n_imagens_baseline, batch_size,
    )
    warmup_epochs_joint = calcular_warmup_epochs_equivalente(
        warmup_steps_alvo, n_imagens_joint, batch_size,
    )

    # a fração de época necessária é MENOR para o braço com mais imagens/época
    assert warmup_epochs_joint < warmup_epochs_baseline

    passos_reais_baseline = passos_de_warmup_reais(warmup_epochs_baseline, n_imagens_baseline, batch_size)
    passos_reais_joint = passos_de_warmup_reais(warmup_epochs_joint, n_imagens_joint, batch_size)

    assert passos_reais_baseline == pytest.approx(warmup_steps_alvo, rel=1e-9)
    assert passos_reais_joint == pytest.approx(warmup_steps_alvo, rel=1e-9)
    assert passos_reais_baseline == pytest.approx(passos_reais_joint, rel=1e-9)


def test_bug_reproduzido_sem_a_correcao_para_contraste():
    """Mostra o que aconteceria SEM a correção (warmup em épocas fixas,
    não convertido) -- confirma que o bug documentado é real e não um
    exagero: mesma 'warmup_epochs' nominal, passos reais bem diferentes."""
    warmup_epochs_fixo = 3.0  # como no protocolo antigo, "3 épocas de warmup"
    batch_size = 16
    n_imagens_baseline = 1348
    n_imagens_joint = 1348 * 2

    passos_baseline = passos_de_warmup_reais(warmup_epochs_fixo, n_imagens_baseline, batch_size)
    passos_joint = passos_de_warmup_reais(warmup_epochs_fixo, n_imagens_joint, batch_size)

    # sem a correção, o braço joint recebe o DOBRO de passos de warmup --
    # exatamente o tipo de discrepância documentada no changelog do
    # projeto anterior (252 steps vs. 26x mais)
    assert passos_joint == pytest.approx(2 * passos_baseline, rel=1e-9)


def test_gerar_kwargs_treino_usa_warmup_convertido_e_patience_desabilitado():
    protocolo = ProtocoloTreinoV2(
        pesos_base="yolo11n.pt", epochs_total=300, epoca_checkpoint=250,
        warmup_steps_alvo=500, batch_size=16,
    )
    kwargs = gerar_kwargs_treino(protocolo, n_imagens_epoca_deste_braco=1348, nome_braco="B2", seed=42)

    assert kwargs["epochs"] == 300
    assert kwargs["patience"] == 301  # epochs_total + 1 -- nunca esgota dentro do cronograma
    assert kwargs["seed"] == 42
    assert kwargs["name"] == "B2_seed42"
    assert kwargs["_epoca_checkpoint_a_usar"] == 250

    # confirma que o warmup_epochs calculado reproduz o warmup_steps_alvo
    passos = passos_de_warmup_reais(kwargs["warmup_epochs"], 1348, 16)
    assert passos == pytest.approx(500, rel=1e-9)


def test_gerar_kwargs_treino_dois_bracos_mesmo_warmup_steps_diferentes_warmup_epochs():
    protocolo = ProtocoloTreinoV2(
        pesos_base="yolo11n.pt", epochs_total=300, epoca_checkpoint=250, warmup_steps_alvo=500,
    )
    kwargs_b2 = gerar_kwargs_treino(protocolo, n_imagens_epoca_deste_braco=1348, nome_braco="B2", seed=42)
    kwargs_joint = gerar_kwargs_treino(protocolo, n_imagens_epoca_deste_braco=1348 * 2, nome_braco="A_joint", seed=42)

    assert kwargs_b2["warmup_epochs"] != kwargs_joint["warmup_epochs"]
    # mas os passos reais resultantes devem ser iguais entre os dois braços
    passos_b2 = passos_de_warmup_reais(kwargs_b2["warmup_epochs"], 1348, protocolo.batch_size)
    passos_joint = passos_de_warmup_reais(kwargs_joint["warmup_epochs"], 1348 * 2, protocolo.batch_size)
    assert passos_b2 == pytest.approx(passos_joint, rel=1e-9)

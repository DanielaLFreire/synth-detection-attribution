"""
Protocolo de treino V2 (tarefa -1.5, §3 do plano).

Corrige um bug documentado do projeto anterior: warmup configurado em
ÉPOCAS produz quantidades de aquecimento diferentes entre braços com
tamanhos de dataset diferentes (ex.: braço "joint", com dados reais +
sintéticos, tem o dobro de passos por época do que o baseline) --
documentado em docs/CHANGELOG_metodologico.md como a causa da comparação
inválida entre B2 (252 steps de warmup) e os braços joint (26x mais).

Este módulo define o warmup em PASSOS DE GRADIENTE ABSOLUTOS, e calcula,
para cada braço, a fração de época equivalente -- de modo que todos os
braços recebam exatamente o mesmo aquecimento, independente do tamanho do
dataset daquele braço específico.

Duas outras regras impostas por este módulo (não apenas documentadas):
- `early_stopping_habilitado` é sempre False -- o treino sempre roda o
  cronograma completo. Early stopping por métrica de validação é, na
  prática, seleção de checkpoint informada pelo val (mesmo problema
  discutido para o Estágio A, ver docs/CHANGELOG_metodologico.md,
  2026-09-01).
- `epoca_checkpoint` é um campo OBRIGATÓRIO, sem valor padrão -- deve vir
  de observação de convergência na piloto (Fase 1), nunca escolhido por
  conveniência ou copiado de outro projeto sem re-verificação.
"""
from __future__ import annotations

from dataclasses import dataclass, field


class ProtocoloInvalido(ValueError):
    """Levantado quando a configuração do protocolo é internamente
    inconsistente (ex.: checkpoint além do total de épocas)."""


@dataclass(frozen=True)
class ProtocoloTreinoV2:
    """Configuração do protocolo de treino V2, comum a todos os braços.

    Os hiperparâmetros de otimização (optimizer, lr0, lrf, cos_lr, imgsz,
    batch_size) são os documentados como usados na campanha original (ver
    docs/referencias_metodologicas.md / CHANGELOG do projeto anterior) --
    manter esses fixos entre braços não é o que estava quebrado; o que
    estava quebrado é o warmup e a seleção de checkpoint, corrigidos aqui.
    """
    # --- otimização (mantido do protocolo original, não é o que quebrou) ---
    pesos_base: str            # ex.: "yolo11n.pt" (pré-treino COCO)
    optimizer: str = "AdamW"
    lr0: float = 0.001
    lrf: float = 0.01
    cos_lr: bool = True
    imgsz: int = 640
    batch_size: int = 16
    cache: str = "disk"

    # --- correção 1: warmup em passos absolutos, não em épocas ---
    warmup_steps_alvo: int = 500

    # --- correção 2: sem seleção de checkpoint via early stopping ---
    epochs_total: int = 300
    epoca_checkpoint: int | None = None  # OBRIGATÓRIO na prática -- ver __post_init__
    early_stopping_habilitado: bool = False

    def __post_init__(self):
        if self.epoca_checkpoint is None:
            raise ProtocoloInvalido(
                "epoca_checkpoint é obrigatório e não tem valor padrão por "
                "design -- deve ser decidido a partir da convergência "
                "observada na piloto (Fase 1), nunca copiado de outro "
                "projeto ou escolhido sem evidência. Ver §3 do plano."
            )
        if self.epoca_checkpoint > self.epochs_total:
            raise ProtocoloInvalido(
                f"epoca_checkpoint ({self.epoca_checkpoint}) não pode ser "
                f"maior que epochs_total ({self.epochs_total})."
            )
        if self.early_stopping_habilitado:
            raise ProtocoloInvalido(
                "early_stopping_habilitado=True viola o protocolo V2: "
                "isso equivale a selecionar o checkpoint pelo desempenho "
                "no val, o problema que este protocolo existe para evitar."
            )
        if self.warmup_steps_alvo <= 0:
            raise ProtocoloInvalido("warmup_steps_alvo deve ser positivo.")


def calcular_warmup_epochs_equivalente(
    warmup_steps_alvo: int, n_imagens_epoca: int, batch_size: int,
) -> float:
    """Converte um número-alvo de passos de warmup (constante entre
    braços) para a fração de época equivalente NESTE braço específico --
    que depende de quantas imagens este braço tem por época.

    Esta é a função que resolve o bug: dois braços com warmup_steps_alvo
    igual, mas n_imagens_epoca diferente, recebem warmup_epochs diferente
    (calculado aqui) para terminarem com o MESMO número real de passos.
    """
    if n_imagens_epoca <= 0 or batch_size <= 0:
        raise ValueError("n_imagens_epoca e batch_size devem ser positivos")
    passos_por_epoca = n_imagens_epoca / batch_size
    return warmup_steps_alvo / passos_por_epoca


def passos_de_warmup_reais(warmup_epochs: float, n_imagens_epoca: int, batch_size: int) -> float:
    """Inverso de calcular_warmup_epochs_equivalente -- usado só em teste,
    para confirmar que dois braços diferentes produzem o mesmo número de
    passos reais de warmup a partir dos warmup_epochs calculados."""
    passos_por_epoca = n_imagens_epoca / batch_size
    return warmup_epochs * passos_por_epoca


def gerar_kwargs_treino(
    protocolo: ProtocoloTreinoV2,
    n_imagens_epoca_deste_braco: int,
    nome_braco: str,
    seed: int,
) -> dict:
    """Monta o dicionário de argumentos de treino para este braço
    específico, com o warmup já convertido para a fração de época correta.

    Assume framework estilo Ultralytics YOLO (mesmo usado na linhagem
    deste projeto -- ver docs/referencias_metodologicas.md). Se outro
    framework for adotado, só esta função precisa mudar; o resto do
    protocolo (ProtocoloTreinoV2) é agnóstico de framework.
    """
    warmup_epochs = calcular_warmup_epochs_equivalente(
        protocolo.warmup_steps_alvo, n_imagens_epoca_deste_braco, protocolo.batch_size,
    )

    # patience: o framework subjacente pode não aceitar 0 de forma
    # confiável para "desabilitar" early stopping (comportamento
    # documentado como incerto em algumas versões do Ultralytics). Usamos
    # epochs_total + 1 -- garante matematicamente que a paciência nunca é
    # esgotada dentro do cronograma, sem depender de um "modo especial" de
    # flag que pode ter semântica ambígua entre versões de biblioteca.
    patience_efetivo = protocolo.epochs_total + 1

    return {
        "model": protocolo.pesos_base,
        "epochs": protocolo.epochs_total,
        "patience": patience_efetivo,
        "batch": protocolo.batch_size,
        "imgsz": protocolo.imgsz,
        "optimizer": protocolo.optimizer,
        "lr0": protocolo.lr0,
        "lrf": protocolo.lrf,
        "cos_lr": protocolo.cos_lr,
        "warmup_epochs": warmup_epochs,
        "cache": protocolo.cache,
        "seed": seed,
        "name": f"{nome_braco}_seed{seed}",
        # checkpoint a usar depois do treino: sempre a época pré-registrada,
        # nunca "best.pt" (que o Ultralytics escolhe por métrica de val)
        "_epoca_checkpoint_a_usar": protocolo.epoca_checkpoint,
    }

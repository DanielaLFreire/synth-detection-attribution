# Adendo pré-registrado — Fase 3 (Estágio B), fatorial redesenhado

**Status**: FINAL, PRONTO PARA LACRAÇÃO. Lacrado por hash (SHA-256 em
`hashes.json`, entrada separada) e commitado publicamente ANTES de qualquer
construção de célula ou treino da Fase 3. Após a lacração, este arquivo não
é editado; correções vão em novo adendo.

**Relação com o pré-registro original**: `previsoes_fase0.md` permanece
lacrado e intocado. P5 e P6 são refinadas aqui (não substituídas: os
vereditos de P5/P6 originais também serão reportados). P8 e P9 são novas.

---

## 1. Motivação (evidência do Estágio A, fechado em 2026-09-14)

Ver `docs/resultados_estagio_a.md`. Três achados motivam o redesenho:

1. **Efeito de escala não-monotônico e assimétrico**: dependência parcial de
   `log_fator_reescala` em U invertido; ampliação extrema (fator > 20×)
   custa SHAP −0,53, redução extrema (< 0,05×) apenas −0,08. "Descasada"
   agrupa duas condições muito diferentes.
2. **Contraste do crop** é o determinante mais forte no nível do crop (1º
   em 100% das reamostras por grupo, direção +0,93), e o fatorial original
   não o manipulava.
3. **Resolução nativa** é o 2º determinante — mas, com geometria fixa entre
   células, resolução nativa e fator de reescala são o MESMO eixo
   (fator = tamanho_caixa / tamanho_nativo). Não é um fator independente:
   é absorvido pelos níveis de escala ("reduzida" = alta resolução nativa
   reduzida; "ampliada" = baixa resolução nativa ampliada).

## 2. Fatores e níveis

### Fator A — escala (3 níveis), definidos por `fator_reescala` = área da caixa / área nativa do crop

| Nível | Faixa de `fator_reescala` | Significado |
|---|---|---|
| `casada` | [0,5, 2,0] | crop nativo ≈ tamanho da caixa (faixa da Fase 0, config lacrada) |
| `reduzida` | < 0,5 | crop maior que a caixa: alta resolução nativa, reduzido |
| `ampliada` | > 2,0 | crop menor que a caixa: baixa resolução nativa, ampliado |

A distribuição de `fator_reescala` DENTRO de cada nível é registrada por
célula (o Estágio A indica que a penalidade de "ampliada" se concentra
acima de ~8–20×; isso é analisado como secundário, não como fator).

### Fator B — contraste do crop (2 níveis)

`contraste` = desvio padrão da intensidade em escala de cinza, medido SÓ
dentro da máscara (`src/attribution/features.py`), calculado para TODO o
pool das três fontes elegíveis (não só os crops amostrados no Estágio A).

| Nível | Definição |
|---|---|
| `alto` | contraste > mediana do pool elegível |
| `baixo` | contraste ≤ mediana do pool elegível |

O valor exato da mediana é fixado no momento da construção das células e
registrado em `configs/celulas_fase3.json` (gerado pelo script, não editado
à mão), antes de qualquer treino.

### Desenho: 3 × 2 = 6 células, completo (não fracionado)

Nenhuma interação fica confundida com efeito principal.

## 3. Restrições de construção (obrigatórias, verificadas por script)

1. **Mesmas caixas em todas as células.** As células diferem SÓ no crop
   colado. Conjunto de caixas = split de TREINO do CITRA-3D-Real, restrito
   às caixas viáveis em TODAS as 6 células (existe ao menos um crop
   elegível de cada uma das 3 fontes para cada célula). Caixas inviáveis
   em qualquer célula são excluídas de todas. O número e a fração de
   caixas excluídas são reportados.
2. **Fontes: SMD, SeaShips, ABOShips — proporção 1/3 cada, em todas as
   células.** InaTechShips excluído do fatorial inteiro: 0,8% de
   pareamentos `casada` e 0,2% `ampliada` (Fase 0, 20.000 pareamentos) --
   incompatível com 2 dos 3 níveis. Manter proporção de fonte constante
   (§5.7) exige as mesmas fontes em todas as células.
3. **N sintético fixo por célula**: `n_variacoes = 2` × nº de imagens de treino
   viáveis; cada variação compõe todas as caixas viáveis da imagem. Igual
   entre células por construção.
4. **Protocolo de treino**: V2, idêntico ao piloto (YOLO11n, 150 épocas,
   `epoca_checkpoint = 150`, warmup em passos absolutos, seeds 42/123/2024),
   balanceamento 50/50 real:sintético com `repeat_real = n_variacoes`.
5. **Braço de controle**: real sobreamostrado com o MESMO `repeat_real`
   e zero sintéticos (isola repetição do real do efeito da composição).
   B2 (real puro) já existe da Fase 1 como referência.
6. **Sem seleção de checkpoint por validação**: `weights/last.pt` (época
   150), como fechado na Fase 1.

## 4. Métrica e regra de leitura

- Primária na Fase 3: **recall in-domain no split de VALIDAÇÃO** do CITRA,
  época 150. O split de TESTE permanece intocado até a Fase 4, onde é
  avaliado uma única vez.
- Secundária: mAP50 no mesmo split e época.
- **Piso de ruído**: 2,0 pp (Fase 1, banda 1, maior amplitude entre braços).
  Um efeito só é real se a média superar 2,0 pp E o sinal for consistente
  entre as 3 seeds. Sempre reportar deltas por seed.
- **Effect size**: d de Cohen pareado por seed, ao lado de cada delta.

## 5. Previsões (com critérios de confirmação/refutação)

### P5-refinada (substitui a leitura de P5; P5 original também reportada)

**P5a — ampliada é o pior nível.** recall(`ampliada`) < recall(`casada`) e
< recall(`reduzida`), ambos os deltas > 2,0 pp, consistentes entre seeds.
Refutação: qualquer um dos deltas < 2,0 pp ou de direção invertida.

**P5b — casada ≥ reduzida, magnitude incerta.** Direção prevista positiva;
NÃO se prevê que supere o piso de ruído (o Estágio A sugere penalidade
pequena para redução). Confirmação: direção positiva na média e em ≥ 2 de
3 seeds. Refutação: reduzida supera casada por > 2,0 pp.

### P8 — contraste alto supera contraste baixo (nova)

recall(`alto`) − recall(`baixo`) > 2,0 pp, consistente entre seeds, como
efeito principal (média sobre os 3 níveis de escala).
Refutação: delta < 2,0 pp ou invertido.

### P9 — interação escala × contraste (exploratória, sem direção)

Sem previsão direcional. Reportada com IC e effect size; qualquer leitura
é exploratória e assim rotulada.

### P6-refinada — efeitos são robustos fonte a fonte

Com as 3 fontes balanceadas em todas as células, os efeitos principais
(P5a, P8) mantêm a direção quando calculados restringindo os sintéticos a
cada fonte isoladamente (análise secundária). Refutação: um efeito
principal inverte de direção ao remover uma única fonte.

### P10 — nenhuma célula supera o controle real-sobreamostrado por > 2,0 pp? (NÃO é previsão; é a questão que a Fase 3 responde)

Registrado explicitamente para evitar leitura post-hoc: o piloto da Fase 1
mostrou `controle` > `A_joint` (pool inteiro, sem estratificação). A Fase
3 responde se alguma célula ESTRATIFICADA supera o controle. Sem previsão
direcional pré-registrada; resultado reportado como está.

## 6. Árvore de hipóteses e correção múltipla (Holm–Bonferroni por família)

| Família | Testes | Ordem |
|---|---|---|
| F1 — efeitos principais confirmatórios | P5a (ampliada vs casada), P5a (ampliada vs reduzida), P8 | 3 testes |
| F2 — secundários | P5b, P6-refinada (por fonte) | reportados com correção própria |
| F3 — exploratórios | P9, P10, distribuição intra-nível de `fator_reescala` | sem inferência confirmatória |

Teste primário: ANOVA fatorial 3×2 com seed como bloco; t pareado por seed
para contrastes; leave-one-seed-out de rotina.

## 7. Orçamento de GPU (medido no piloto: A100, ~8,5 it/s)

Piloto: A_joint com 35.048 imgs/época levou **~10,2 h por seed**; B2
(1.348 imgs/época) ~0,42 h. Tempo ≈ proporcional às imagens por época.

| `n_variacoes` | imgs/época (50/50) | h por execução | 6 células × 3 seeds | + controle × 3 | **Total** |
|---|---|---|---|---|---|
| 1 | 2.696 | ~0,8 | ~14 h | ~2,4 h | **~17 h** |
| 2 | 5.392 | ~1,6 | ~28 h | ~4,7 h | **~33 h** |
| 3 | 8.088 | ~2,4 | ~42 h | ~7,1 h | **~49 h** |

Cada execução salva no Drive ao terminar (correção da Fase 1); a Fase 3
tolera desconexões — só a execução em andamento se perde.

**Poder**: com o piso de 2,0 pp e 3 seeds, efeitos menores que ~2,5–3 pp
podem não ser distinguíveis. `n_variacoes` menor reduz custo mas também o
volume sintético por célula, o que pode reduzir a magnitude dos efeitos.
Não há como saber a priori; a escolha é de orçamento, e é registrada
como tal.

**DECISÃO FIXADA em 2026-09-14 (usuário): `n_variacoes = 2`** — equilíbrio
entre custo (~33 h de GPU) e volume sintético (2.696 imagens por célula,
~2× o real). Registrada como escolha de orçamento, não de poder estatístico.

## 8. O que este adendo NÃO muda

- Nada do Estágio A é reanalisado. Nada do pré-registro original é editado.
- O split de teste do CITRA continua intocado.
- O segundo domínio (UA-DETRAC, P7) permanece na Fase 4, sem alteração —
  com a expectativa adicional (registrada no Estágio A) de que
  `coerencia_escala_pos` seja testável lá, por haver gradiente de
  perspectiva.

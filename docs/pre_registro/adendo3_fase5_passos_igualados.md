# Adendo 3 pré-registrado — Fase 5: composição sintética vs. real com passos de otimização igualados

**Status**: FINAL, PRONTO PARA LACRAÇÃO (SHA-256 em `hashes.json`, entrada
separada; commit público antes de qualquer alteração de código de treino,
construção de trainlist ou execução de GPU desta fase).

**Relação com os registros anteriores**:
- `previsoes_fase0.md`, `adendo_fase3_fatorial.md` (adendo 1) e
  `adendo2_fase3_fatorial_2x2.md` (adendo 2): intocados. Os vereditos da
  Fase 3 e da Fase 4 permanecem registrados como foram emitidos.
- Este adendo NÃO reabre nem reinterpreta a letra de P10. Ele testa uma
  explicação alternativa para P10 que o desenho do adendo 2 não excluía.
- A tag `v1.0-experimento-fechado` continua marcando o estado fechado das
  Fases 0 a 4. Esta fase termina com tag própria.

---

## 1. Motivação: o confundimento que o adendo 2 não controlou

No adendo 2 (§3.6–3.7) todos os braços treinaram 150 épocas fixas, com
warmup igualado em passos absolutos, mas com número de imagens por época
diferente:

| Braço (Fase 3) | Imagens/época | Passos/época (batch 16) | Passos totais |
|---|---|---|---|
| B2, real × 1 (Fase 1) | 1.348 | 85 | 12.750 |
| controle, real × 2 | 2.696 | 169 | 25.350 |
| células, real × 2 + 2.592 sintéticas | 5.288 | 331 | 49.650 |

As células receberam ~1,96× os passos de otimização do controle. O
resultado P10 (células − controle = −1,80 pp em val, −1,75 pp em teste,
12/12 pares negativos) é, portanto, compatível com duas explicações que o
desenho não separa:

- **(a) conteúdo**: a imagem sintética é pior que a real como dado de
  treino;
- **(b) passos**: o braço com sintéticas foi mais longe na fase de
  sobreajuste, por ter o dobro de passos no mesmo cronograma.

Evidências a favor de que (b) é plausível, todas já registradas:
- o changelog da Fase 1 (2026-09-09) registra que braços com mais
  imagens/época convergem mais rápido;
- no pico (F3, exploratório), células e controle empatam (−0,15 a −0,57
  pp, sinais mistos);
- medido em passos, e não em épocas, o pico das células (épocas 85–114,
  ~28.000–37.700 passos) ocorre DEPOIS do pico do controle (época 130,
  ~22.000 passos);
- no teste, células − B2 = −0,57 pp: ordem B2 < controle > células,
  compatível com uma curva em U invertido em função dos passos.

A replicação no teste exclui ruído de seed, mas não exclui (b): validação
e teste herdam o mesmo desequilíbrio de passos.

## 2. Pergunta

Com o MESMO número de passos de otimização, o mesmo cronograma de taxa de
aprendizado e a mesma composição de época, substituir parte do fluxo de
imagens reais repetidas por imagens com composição sintética melhora,
piora ou não altera o recall in-domain no CITRA-3D-Real?

## 3. Mudança conceitual

Com passos fixos, "real × 1" e "real × 2" deixam de ser tratamentos
distintos: repetir a lista só altera a ordem de amostragem. O controle
passa a ser **real puro com S passos**, e o fator manipulado passa a ser a
**fração sintética p no fluxo de amostras**.

## 4. Desenho: orçamento (2) × fração sintética (3), 5 seeds

### 4.1 Fatores

| Fator | Níveis |
|---|---|
| Orçamento S | S1 = 30 épocas × 337 passos = **10.110 passos**; S2 = 75 épocas × 337 passos = **25.275 passos** |
| Fração sintética p | **0** (C), **0,25** (M25), **0,50** (M50) |

S2 reproduz, com diferença de −0,3%, o orçamento do controle da Fase 3
(25.350 passos). S1 fica na faixa do orçamento e do pico do B2. A razão
S2/S1 = 2,5 dá alavanca para o teste de interação (P13).

### 4.2 Composição da trainlist: comprimento fixo L = 5.392 em todos os braços

| Braço | Real | Sintético | Total | p |
|---|---|---|---|---|
| C | 1.348 × 4 = 5.392 | 0 | 5.392 | 0,00 |
| M25 | 1.348 × 3 = 4.044 | 1.348 | 5.392 | 0,25 |
| M50 | 1.348 × 2 = 2.696 | 2.696 | 5.392 | 0,50 |

- Todas as imagens reais de treino aparecem com o MESMO peso dentro de
  cada braço. Nenhuma imagem real é sub- ou sobreponderada.
- Passos por época = ⌈5.392 / 16⌉ = 337 em todos os braços. Dentro de cada
  orçamento, épocas, passos, warmup e `close_mosaic` são idênticos entre
  braços. A única diferença entre braços é o conteúdo da trainlist.

### 4.3 Conjunto sintético

- Origem: as imagens sintéticas já geradas das 4 células da Fase 3
  (2.592 por célula, após a remoção de cópias sem colagem, commit
  `d82223d`). Nenhuma composição nova é gerada.
- Justificativa: escala e contraste foram nulos no teste. Não há critério
  pré-registrado que justifique escolher uma célula; escolher a que
  "parecia melhor no pico" seria seleção post hoc.
- **M50**: 2.696 imagens únicas, amostra estratificada de **674 por
  célula**, sem reposição, semente de amostragem **20260928**.
- **M25**: 1.348 imagens, subconjunto ANINHADO de M50 (as primeiras 337
  de cada célula na ordem da amostragem). O aninhamento garante que a
  diferença entre M25 e M50 é só de dose.
- O manifesto da amostra (caminho, célula, imagem-base, SHA-256 do
  arquivo) é gerado e tem seu hash registrado em `hashes.json` ANTES do
  primeiro treino.

### 4.4 Protocolo de treino

Herdado do protocolo V2 (YOLO11n pré-treinado COCO, 640, batch 16, AdamW,
lr0 = 0,001, lrf = 0,01, `cos_lr`, `cache = disk`, sem early stopping), com
as seguintes especificações desta fase:

- **Épocas**: 30 (S1) ou 75 (S2).
- **Warmup**: 500 passos absolutos, isto é, `warmup_epochs` = 500 / 337 ≈
  1,4837 em todos os braços.
- **`close_mosaic`**: passa a ser argumento EXPLÍCITO, fixado em 1/15 do
  total de épocas: **2** (S1) e **5** (S2). Na Fase 3 ele não era passado
  (padrão do Ultralytics, 10 épocas = 1/15 de 150); a fração é mantida.
- **Checkpoint**: `weights/last.pt` (última época). Nenhuma seleção por
  validação.
- **Seeds**: 42, 123, 2024 (as mesmas das fases anteriores) + **7** e
  **31415** (novas, declaradas aqui).
- A validação por época é mantida apenas para as curvas; ela não afeta o
  treino.

### 4.5 Execuções: lista fechada

6 braços × 5 seeds = **30 execuções**, nomeadas `f5_{S}_{braço}_seed{n}`,
com S ∈ {S1, S2}, braço ∈ {C, M25, M50}, n ∈ {42, 123, 2024, 7, 31415}.
Mais **1 execução de portão** (§8, G2). Nenhuma execução fora desta lista
entra em qualquer análise desta fase.

## 5. Métricas

- **Primária**: recall in-domain no split de validação, no ponto de
  máximo-F1 (mesma definição da Fase 3), na última época.
- **Secundárias**: mAP50; recall no estrato small a 640 (conf ≥ 0,25,
  IoU ≥ 0,5, casamento guloso, mesma definição da F2 da Fase 3); área
  sob a curva recall × passos, normalizada pelo número de passos (resumo
  da trajetória que não exige escolher um checkpoint).
- **Exploratórias**: passo do pico de recall; queda entre o pico e o
  último passo.

## 6. Previsões e regra de decisão

### 6.1 Regra de decisão (substitui a regra "média > piso" nesta fase)

Para cada contraste confirmatório, calcula-se a diferença por seed
(pareada), a média e o IC com t de Student, df = 4:

| Resultado | Veredito |
|---|---|
| IC 95% inteiramente abaixo de 0 | **sintético pior** |
| IC 90% inteiramente dentro de ±1,0 pp (TOST, α = 0,05) | **equivalente** |
| IC 95% inteiramente acima de 0 | **sintético melhor** |
| nenhum dos casos acima | **inconclusivo** |

Um resultado inconclusivo é reportado como tal. Ele não é convertido em
"direção compatível" nem em "tendência". Deltas por seed, d de Cohen
pareado e leave-one-seed-out são sempre reportados.

**Sem parada opcional**: o número de seeds é fixo em 5. Se o
desvio-padrão das diferenças pareadas passar de 0,8 pp, o experimento é
declarado subdimensionado para a margem de ±1,0 pp, e isso é reportado.
Não se adicionam seeds depois de ver o resultado.

### 6.2 P11 (primária): M50 vs. C no orçamento S2

Contraste: recall(M50, S2) − recall(C, S2). Teste bicaudal.

- H−: sintético pior. H0: equivalente. H+: sintético melhor.
- **Expectativa declarada** (não é critério): equivalência, |Δ| < 1 pp,
  com base no empate no pico da Fase 3.
- Execuções que testam P11: `f5_S2_C_*` e `f5_S2_M50_*` (10 execuções).

### 6.3 P12: dose-resposta em S2

Contraste linear (−1, 0, +1) sobre C, M25 e M50 no orçamento S2, por seed.
Veredito pela mesma regra de §6.1, aplicada ao contraste linear dividido
por 2, o que o torna comparável a um delta M50 − C.

- Execuções: `f5_S2_*` (15 execuções).

### 6.4 P13: interação orçamento × fração

Contraste: (M50 − C em S2) − (M50 − C em S1), por seed.

- Sob a hipótese de que o sintético regulariza contra o sobreajuste do
  real repetido, **prevê-se P13 > 0**: vantagem do sintético maior no
  orçamento longo.
- Veredito: "interação positiva" se IC 95% > 0; "interação negativa" se
  IC 95% < 0; caso contrário, "interação não detectada". Nesta previsão
  não se aplica teste de equivalência.
- Execuções: `f5_S1_C_*`, `f5_S1_M50_*`, `f5_S2_C_*`, `f5_S2_M50_*` (20
  execuções).

### 6.5 Interpretação pré-declarada dos desfechos de P11

| P11 | Consequência para a conclusão da Fase 3 |
|---|---|
| sintético pior | P10 passa a valer sem o confundimento de passos: composição < real. |
| equivalente | A desvantagem de P10 é atribuída a passos; composição neutra (sem ganho, sem dano). |
| sintético melhor | A conclusão de P10 se inverte sob passos igualados; exige replicação em outra arquitetura antes de qualquer recomendação operacional. |
| inconclusivo | P10 permanece com o confundimento declarado como limitação. |

## 7. Correção múltipla e famílias

| Família | Testes | Correção |
|---|---|---|
| F1 — confirmatórios | P11, P12, P13 | Holm–Bonferroni sobre os p bicaudais do t pareado. O veredito de P11 segue §6.1; o p de Holm é reportado ao lado. |
| F2 — secundários | P11 no estrato small; P11 em mAP50; P11 na área sob a curva; M50 − C em S1 | Holm dentro da família |
| F3 — exploratórios | passo do pico; M25 vs. M50; C(S2) vs. controle da Fase 3 (não pareado, sanidade) | sem inferência confirmatória |

Análise complementar de F1: ANOVA 2 × 3 (orçamento × fração) com seed
como bloco.

## 8. Portões, em ordem

- **G0 — lacração**: este adendo e sua entrada em `hashes.json` em commit
  público. Recomenda-se registro externo do SHA-256 (e-mail ao
  supervisor ou depósito com carimbo de tempo) no mesmo dia.
- **G1 — código e testes de CPU** (após G0, antes de qualquer GPU):
  - `close_mosaic` explícito no protocolo, com padrão 10 para que as
    configurações da Fase 3 permaneçam inalteradas;
  - construtor de trainlist por fração, com teste que verifica, para os
    3 braços: L = 5.392, peso igual por imagem real, p exato, ⌈L/16⌉ =
    337;
  - script de amostragem do conjunto sintético (§4.3) com manifesto e
    hash;
  - teste de que, dentro de cada orçamento, os kwargs de treino dos 3
    braços diferem APENAS no arquivo de dados.
- **G2 — determinismo sob o código novo**: `f5_S1_C_seed42` executado
  duas vezes; métricas idênticas em todas as colunas exceto tempo. Se
  falhar, a fase para e a divergência é registrada em novo adendo.
- **G3 — integridade de cada execução**: `results.csv` com exatamente o
  número de épocas do orçamento, `last.pt` presente e número de
  iterações no log igual a épocas × 337. Uma execução que falhar é
  refeita com a MESMA seed; nenhuma é descartada seletivamente.

## 9. Split de teste

O teste já foi avaliado uma vez (Fase 4, marcador
`fase4/teste_avaliado.json`). Esta é uma segunda avaliação, legítima pela
regra do projeto apenas por estar pré-registrada aqui, com lista fixa:

- **Lista**: os 30 `last.pt` de §4.5. A execução de portão (G2) fica de
  fora.
- **Marcador próprio**: `fase5/teste_avaliado.json`. Uma segunda chamada
  é recusada, como na Fase 4.
- **Verificação pré-avaliação**: isolamento por nome e por conteúdo
  contra train, val e o manifesto da amostra sintética (§4.3).
- **Papel**: as decisões saem da validação. O teste é réplica
  confirmatória. P11 "replica" se o veredito no teste cair na mesma
  categoria de §6.1; caso contrário, reportam-se os dois.

## 10. Orçamento de GPU (A100, ~8,5 it/s, mais a validação por época)

| Execuções | Horas (estimativa) |
|---|---|
| 15 × S1 (10.110 passos, ~0,4 h) | ~6 h |
| 15 × S2 (25.275 passos, ~0,9 h) | ~13,5 h |
| G2: 1 × S1 | ~0,4 h |
| Avaliação no teste | minutos |
| **Total** | **~20 h** |

Os tempos efetivamente medidos são registrados no changelog por
execução, e não este orçamento.

## 11. O que este adendo não muda

Nada nas Fases 0 a 4; nenhum veredito já emitido; o Estágio A; o
segundo domínio (UA-DETRAC, P7). O método de composição também não muda:
nada de large-scale jitter, blending ou novas variações por caixa. Este
adendo testa o MESMO método sob comparação com passos igualados. Mudanças
no método seriam outra pergunta, com adendo próprio.

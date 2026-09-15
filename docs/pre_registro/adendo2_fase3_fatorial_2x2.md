# Adendo 2 pré-registrado — Fase 3 (Estágio B), fatorial 2 × 2

**Status**: FINAL, PRONTO PARA LACRAÇÃO (SHA-256 em `hashes.json`, entrada
separada; commit público antes de qualquer construção de célula ou treino).

**Relação com os registros anteriores**:
- `previsoes_fase0.md` (lacrado): intocado. P5 e P6 originais continuam
  sendo reportadas.
- `adendo_fase3_fatorial.md` (adendo 1, commit `efd4699`, lacrado): o
  fatorial 3 × 2 ali definido foi **rejeitado pela verificação de
  viabilidade da tarefa 3.2**, conforme o critério (b) que o próprio
  adendo 1 e o changelog de 2026-09-14 fixaram antes do resultado. Este
  adendo 2 SUPERSEDE a estrutura fatorial do adendo 1 e HERDA tudo o mais
  (protocolo, métrica, piso de ruído, seeds, `n_variacoes = 2`, fontes,
  árvore de hipóteses no que se aplica). Nenhum treino foi iniciado sob o
  adendo 1.

---

## 1. Por que o 3 × 2 foi rejeitado (evidência, tarefa 3.2, 2026-09-15)

Pool elegível (min_dim_px = 20): 41.426 crops (SMD 6.679, SeaShips 8.863,
ABOShips 25.884). Caixas de treino: 4.489 em 1.348 imagens.

- Viáveis nas 6 células: 2.711 (60,4%). Gargalo: `ampliada`.
- **Exclusão sistemática das menores** (referencial letterbox 640, o do
  detector e do perfil da Fase 0): caixas excluídas com lado mediano
  **8,3 px** (96,9% small); viáveis com lado mediano 22,4 px (72,0%
  small, contra 82,2% do alvo). O 3 × 2 descartaria os 40% menores
  objetos — o caso central de um alvo de vigilância marítima.
- **Causa física, não amostral**: com crops de lado ≥ 20 px (área ≥ 400,
  pior caso 680 px²), `ampliada` (fator > 2 ⇔ área do crop < A/2) exige
  caixa com A > 1.360 px² nativos (lado > 37 px nativos ≈ 12 px a 640).
  Nenhum objeto abaixo disso pode ser "ampliado" com crops de qualidade
  mínima. Consequência para o Estágio A: a penalidade de "ampliação
  extrema" (fator > 20, SHAP −0,53) só ocorreu em caixas > 8.000 px²
  nativos — é um fenômeno de caixas grandes.
- **Registro de erro corrigido**: a primeira leitura desta verificação
  (changelog 2026-09-15) afirmou "0% small sobreviveu", misturando área
  nativa com o limiar de 32 px do referencial 640. Corrigido antes deste
  adendo; os números acima são os do referencial correto.

## 2. Fatores e níveis

### Fator A — escala (2 níveis), `fator_reescala` = área da caixa / área nativa do crop

| Nível | Faixa | Significado |
|---|---|---|
| `casada` | [0,5, 2,0] | crop nativo ≈ tamanho da caixa |
| `reduzida` | < 0,5 | crop maior que a caixa: alta resolução nativa, reduzido |

`ampliada` (> 2,0) **deixa de ser fator manipulado**: não é testável no
regime do alvo (§1). A distribuição de `fator_reescala` dentro de
`reduzida` é registrada por célula (secundário: `reduzida` agrupa
reduções moderadas e extremas).

### Fator B — contraste do crop (2 níveis), medido só na máscara

| Nível | Definição |
|---|---|
| `alto` | contraste > **40,89185** (mediana do pool elegível, fixada pelo script) |
| `baixo` | contraste ≤ 40,89185 |

### Desenho: 2 × 2 = 4 células, completo. Nenhuma confusão de efeitos.

## 3. Construção (verificada por `scripts/verificar_celulas_fase3.py`; artefato `configs/celulas_fase3.json`)

1. **Mesmas caixas em todas as células**: as **3.987 caixas** (88,8% de
   4.489) viáveis nas 4 células com **≥ 2 crops elegíveis por fonte**
   (`minimo_por_fonte = 2`, para que `n_variacoes = 2` não repita crop).
   Em **1.296 imagens** de treino. Lista em `caixas_viaveis_fase3.csv`.
   - Viáveis: lado mediano 16,0 px a 640, **82,3% small** (alvo: 82,2%).
   - Excluídas (502): lado mediano 5,3 px a 640 (cauda inferior) e
     algumas caixas gigantes sem crop `casada` em alguma fonte.
2. **Caixas não viáveis dentro de imagens viáveis** permanecem com o
   objeto REAL e sua anotação real, identicamente em todas as células.
   Nunca são removidas da anotação (seriam falsos negativos de treino).
3. **Fontes: SMD, SeaShips, ABOShips, 1/3 cada, em todas as células.**
   InaTechShips excluído (0,8% `casada`; §1 do adendo 1).
4. **Sorteio**: para cada (caixa, variação), fonte sorteada uniforme entre
   as 3; crop sorteado uniforme entre os elegíveis da fonte para a célula
   (nível de escala pela área da caixa; nível de contraste), com semente
   fixa por célula, registrada no manifesto.
5. **N sintético por célula**: 2 variações × 1.296 imagens = **2.592**
   imagens sintéticas, igual entre células por construção.
6. **Treino**: protocolo V2 idêntico ao piloto (YOLO11n, 150 épocas,
   `epoca_checkpoint = 150`, warmup em passos absolutos, seeds 42/123/2024),
   balanceamento real:sintético com `repeat_real = 2` (2.696 real × 2 vs
   2.592 sintético ≈ 51/49).
7. **Controle**: real sobreamostrado (`repeat_real = 2`), zero sintéticos,
   3 seeds. B2 da Fase 1 como referência adicional.
8. **Sem seleção de checkpoint por validação**: `weights/last.pt`.

## 4. Métrica e regra de leitura (herdadas do adendo 1)

Primária: recall in-domain no split de **validação**, época 150; teste
intocado até a Fase 4. Secundária: mAP50. Piso de ruído: **2,0 pp**. Um
efeito é real se a média superar 2,0 pp E o sinal for consistente entre as
3 seeds. d de Cohen pareado ao lado de cada delta. Deltas por seed sempre
reportados. Análise secundária pré-registrada: recall estratificado por
tamanho (small / não-small a 640).

## 5. Previsões

### P5b' — escala: `casada` supera `reduzida` (agora hipótese PRIMÁRIA de escala)

Direção prevista: positiva. Magnitude: incerta; o Estágio A sugere efeito
pequeno (SHAP +0,18 em `casada` vs +0,13/+0,02/−0,08 nas faixas de
`reduzida`).
- **Confirmação forte**: delta > 2,0 pp, mesma direção nas 3 seeds.
- **Confirmação fraca (direção)**: delta > 0 na média e em ≥ 2 de 3
  seeds, mas ≤ 2,0 pp — reportada como "direção compatível, magnitude
  abaixo do piso".
- **Refutação**: `reduzida` supera `casada` por > 2,0 pp, ou direção
  invertida em ≥ 2 de 3 seeds.

### P5a — "ampliada é o pior nível": NÃO TESTÁVEL neste desenho

Mantida apenas como achado observacional do Estágio A, restrito a caixas
grandes. Registrada explicitamente para não ser reintroduzida post-hoc.

### P8 — contraste `alto` supera `baixo`

recall(`alto`) − recall(`baixo`) > 2,0 pp, mesma direção nas 3 seeds,
como efeito principal (média sobre os 2 níveis de escala).
Refutação: delta < 2,0 pp ou invertido.

### P9 — interação escala × contraste: exploratória, sem direção.

### P6' — robustez fonte a fonte

Os efeitos principais (P5b', P8) mantêm a direção quando os sintéticos são
restritos a cada fonte (análise secundária). Refutação: inversão ao
remover uma única fonte.

### P10 — alguma célula supera o controle real-sobreamostrado por > 2,0 pp?

Questão registrada, sem previsão direcional (o piloto mostrou
`controle` > `A_joint` com pool não estratificado).

## 6. Árvore de hipóteses e correção múltipla (Holm–Bonferroni por família)

| Família | Testes |
|---|---|
| F1 — confirmatórios | P5b' (casada vs reduzida), P8 (alto vs baixo) — 2 testes |
| F2 — secundários | P6' por fonte; recall estratificado por tamanho |
| F3 — exploratórios | P9, P10, distribuição de `fator_reescala` em `reduzida` |

ANOVA 2 × 2 com seed como bloco; t pareado por seed para contrastes;
leave-one-seed-out.

## 7. Orçamento de GPU

Imagens por época ≈ 2.592 + 2.696 = 5.288 → ~1,5 h por execução (A100,
proporcional ao piloto: 35.048 imgs/época ≈ 10,2 h).

| Execuções | Horas |
|---|---|
| 4 células × 3 seeds | ~18 h |
| controle × 3 seeds | ~4,5 h |
| **Total** | **~23 h** (adendo 1 previa ~33 h para 6 células) |

Cada execução salva no Drive ao terminar; tolera desconexões.

## 8. O que este adendo não muda

Nada do Estágio A; nada do pré-registro original; split de teste intocado;
segundo domínio (UA-DETRAC, P7) inalterado.

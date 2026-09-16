# Resultados da Fase 3 (Estágio B) — confronto com o adendo 2

Fechamento: 2026-09-16. Adendo 2 lacrado em `a4ec7ab` (SHA-256
`be395b8b…`); nenhum treino iniciado antes. 15 execuções íntegras (4
células + controle × seeds 42/123/2024), 150 épocas cada, `weights/last.pt`.
Métrica primária: recall in-domain no split de validação, época 150. Piso
de ruído: 2,0 pp. Split de teste intocado.

## 1. Dados

| Braço | seed 42 | seed 123 | seed 2024 | média ± dp |
|---|---|---|---|---|
| casada__alto | 0,6938 | 0,6923 | 0,6827 | 0,6896 ± 0,0060 |
| casada__baixo | 0,6855 | 0,7056 | 0,6868 | 0,6926 ± 0,0112 |
| reduzida__alto | 0,6796 | 0,6975 | 0,6717 | 0,6829 ± 0,0132 |
| reduzida__baixo | 0,6851 | 0,6953 | 0,6697 | 0,6834 ± 0,0129 |
| controle (real × 2) | 0,7017 | 0,7151 | 0,6985 | **0,7051** ± 0,0088 |

ANOVA 2 × 2 com seed como bloco: escala F(1,6) = 5,59, p = 0,056;
contraste F = 0,28, p = 0,62; interação F = 0,15, p = 0,72; **seed F(2,6) =
11,8, p = 0,008** (o bloco por seed é necessário — o piso de ruído da
Fase 1 não era excesso de cautela).

## 2. Vereditos pela letra do adendo 2 (§5)

| Previsão | Critério | Resultado (média, por seed) | Veredito |
|---|---|---|---|
| **P5b'** casada > reduzida | forte: > 2,0 pp e mesma direção nas 3 seeds; fraca: > 0 na média e em ≥ 2/3 seeds | **+0,80 pp** [+0,73, +0,25, +1,41]; d = 1,37; p = 0,14 (Holm 0,28) | **Confirmação fraca** — direção compatível nas 3 seeds, magnitude abaixo do piso |
| **P8** contraste alto > baixo | > 2,0 pp, mesma direção nas 3 seeds | **−0,18 pp** [+0,14, −0,56, −0,11]; p = 0,48 | **Refutada** — efeito nulo |
| **P9** interação | exploratória | −0,26 pp [+1,38, −1,55, −0,60] | Ruído (como esperado) |
| **P10** alguma célula supera o controle? | questão, sem previsão | Nenhuma. Todas abaixo em **12/12** pares seed×célula. Média −1,80 pp [−1,57, −1,74, −2,08]; d = −6,95; p = 0,007. `reduzida__alto` −2,22 e `reduzida__baixo` −2,17 passam o critério "real"; `casada__*` −1,55 / −1,24 (direção) | **Não: composição < real sobreamostrado**, consistentemente |
| **P6'** robustez fonte a fonte | efeitos mantêm direção com sintéticos restritos a cada fonte | — | **Não testável — erro de desenho do adendo 2**: exige treinos com sintético de uma fonte só (36 execuções), não orçados. Registrado como falha do adendo, não como resultado |
| **P5a** ampliada é o pior | — | — | Não testável neste regime (adendo 2 §5), como previsto |

### Vereditos das previsões originais (pré-registro lacrado da Fase 0), que o adendo prometeu reportar

| Previsão original | Resultado | Veredito |
|---|---|---|
| **P5** escala casada supera descasada acima do piso | casada − reduzida = +0,80 pp < 2,0 | **Refutada** pela letra (direção certa, magnitude abaixo do piso) |
| **P6** assimetria de InaTechShips não distorce o efeito de escala | InaTechShips excluído do fatorial (proporções iguais por desenho) | **Não aplicável** — resolvida por desenho, não testada |

## 3. Análises secundárias e exploratórias

- **F2 — recall estratificado por tamanho** (conf ≥ 0,25, IoU ≥ 0,5,
  casamento guloso; estrato a 640): val tem 1.086 small (85,7%) e 181
  não-small. **Caveat obrigatório**: o piso de 2,0 pp foi calibrado em
  1.267 caixas; no estrato de 181, uma caixa = 0,55 pp e a flutuação
  binomial de uma execução é ~2,5 pp — vereditos "real" nesse estrato
  NÃO são confiáveis pelo critério pré-registrado.
  - *Small*: células − controle **−0,70 pp** (−0,21 a −1,10) — dentro do
    ruído, ≈ neutro. Contraste +0,57 pp (3/3 seeds). Escala +0,32 (mista).
  - *Não-small*: células − controle −2,44 pp (−1,47 a −3,13); contraste
    +1,01 pp (3/3); escala −0,64 (mista).
  - Leitura: o prejuízo agregado (−1,8 pp) vem sobretudo dos objetos
    não-small; no regime dominante do alvo a composição é ≈ neutra.
    Contraste tem direção positiva consistente a limiar fixo, mas < 1 pp
    e de sinal oposto na métrica primária (limiar de máximo-F1): nulo a
    minúsculo, dependente do ponto de operação. Nenhum estrato mostra
    célula acima do controle.
- **F3 — no pico** (seleção informada por validação; NUNCA primária): pico
  médio casada 0,713, reduzida 0,709–0,711, controle 0,715. No pico,
  célula − controle = −0,15 a −0,57 pp, sinais mistos: **empate**. Época
  média do pico: células 85–114, controle 130. Queda pico→150: células
  2,0–2,7 pp, controle 1,0 pp.
- **Contexto (exploratório)**: controle (real × 2) − B2 da Fase 1 (real
  × 1) = +1,67 pp [+0,71, +2,42, +1,89]; o controle tem 2× os passos de
  otimização.

## 4. Leitura substantiva (separada dos vereditos)

1. **Composição sintética não supera repetir o real.** No volume
   pré-registrado (2.592 sintéticas vs 2.696 reais × 2), todas as 4
   células ficam abaixo do controle em 12/12 comparações pareadas — o
   resultado mais consistente do projeto. Isso replica, com
   estratificação por escala e contraste, o que o piloto da Fase 1 já
   mostrava com o pool inteiro.
2. **Mecanismo, pela análise exploratória**: a composição não abaixa o
   teto (no pico, empate) — **acelera o sobreajuste**. As células atingem
   o pico 20–45 épocas antes do controle e degradam 2–3× mais até a
   época fixa. Uma leitura com checkpoint escolhido por validação teria
   escondido isso; a época fixa (decisão da Fase 1) o expôs.
3. **Escala importa na direção prevista, mas pouco**: +0,80 pp a favor de
   `casada`, consistente nas 3 seeds e coerente com o Estágio A (efeito
   secundário, não dominante). Abaixo do piso: não distinguível de ruído
   pelo critério pré-registrado.
4. **Contraste — o achado central sobre o método.** Contraste foi a
   feature de crop MAIS forte para detectabilidade no Estágio A (1º em
   100% das reamostras, direção +0,93). Manipulado no treino: **−0,18 pp,
   nulo**. Logo: *o que torna um objeto colado reconhecível por um
   detector treinado no real não é o que o torna útil para treinar um
   detector*. O alvo-proxy do Estágio A (acerto do B2) mede
   plausibilidade, não utilidade de treino. Esta é a contribuição
   metodológica principal: atribuição observacional sobre um proxy de
   detectabilidade NÃO substitui manipulação causal da utilidade de
   treino — e o desenho em dois estágios foi o que permitiu ver a
   divergência.
5. **O efeito de seed é grande** (F = 11,8): sem 3 seeds e bloco por
   seed, qualquer célula isolada poderia "vencer" ou "perder" por acaso.

## 5. Limitações (a reportar)

- Um volume sintético (2.592) e uma razão real:sintético (~1:1); não se
  testou se volumes maiores ou menores mudam o quadro.
- Um detector (YOLO11n), um cronograma (150 épocas), uma resolução (640).
- `reduzida` agrupa reduções moderadas e extremas (p05 do fator ≈ 0,02).
- P6' não testada (erro do adendo). Estrato não-small pequeno demais (181) para o piso.
- Métrica no split de validação; o teste é avaliado uma vez na Fase 4.

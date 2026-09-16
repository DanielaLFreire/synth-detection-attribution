# Resultados da Fase 4 — avaliação única no split de teste

Avaliado em 2026-09-16T13:31:32Z, commit `53066ad`, marcador
`fase4/teste_avaliado.json`. Verificação prévia GO 7/7 (isolamento por
nome, por conteúdo md5, e contra os 7 manifestos do projeto). Teste: 401
imagens, 1.247 caixas (996 small a 640 = 79,9%). Lista fixa de 18 modelos
(15 da Fase 3 + 3 B2 da Fase 1), `last.pt` (época 150). Métrica primária:
recall no ponto de máximo-F1 (mesma definição de val).

## Recall no teste (média ± dp das 3 seeds) e comparação com val

| Braço | Teste | Val | Δ teste−val |
|---|---|---|---|
| controle (real × 2) | **0,7309** ± 0,0058 | 0,7051 | +2,6 pp |
| B2 (real × 1, Fase 1) | 0,7191 ± 0,0050 | 0,6883 | +3,1 pp |
| casada__alto | 0,7171 ± 0,0016 | 0,6896 | +2,8 pp |
| reduzida__baixo | 0,7152 ± 0,0077 | 0,6834 | +3,2 pp |
| reduzida__alto | 0,7108 ± 0,0044 | 0,6829 | +2,8 pp |
| casada__baixo | 0,7105 ± 0,0125 | 0,6926 | +1,8 pp |

O teste é ligeiramente mais fácil que val (80% vs 86% small); a ordem se
preserva. ANOVA no teste: escala p = 0,88; contraste p = 0,84; interação
p = 0,32; **seed p = 0,96** (em val, p = 0,008 — o bloco por seed de val
não generalizou).

## Vereditos confirmatórios (pela letra do adendo 2, sobre o teste)

| Previsão | Teste (média, por seed) | Veredito final |
|---|---|---|
| P5b' casada > reduzida | +0,08 pp [+0,26, +1,00, −1,02] | **Não confirmada** — a "confirmação fraca" de val (+0,80, 3/3) não replicou; era ruído abaixo do piso |
| P8 contraste alto > baixo | +0,11 pp [+0,61, −0,76, +0,47] | **Refutada** (nula em val e teste) |
| P9 interação | +1,10 pp, mista | Ruído |
| P10 alguma célula supera o controle? | Nenhuma: **−1,75 pp** [−2,39, −1,06, −1,79], 12/12 pares negativos; por célula −1,38 a −2,04 | **Replicado** — o achado robusto do projeto |
| P6' | não testável (erro do adendo) | — |
| P5 original | +0,08 < 2,0 | Refutada |

Referências (exploratórias): controle − B2 = **+1,18 pp** [+1,14, +0,88,
+1,51] (val +1,67); média das células − B2 = **−0,57 pp** [−1,25, −0,18,
−0,28]: sintético + real × 2 ≈ real × 1. F2 (conf ≥ 0,25): small
−0,64 pp (misto), não-small −1,46 pp (misto; 251 caixas, piso não
calibrado) — o padrão "prejuízo concentrado nos não-small" de val
enfraquece no teste; não é robusto.

## Conclusão final do projeto

1. **Composição sintética por recorte-e-colagem não supera repetir o
   real, e neutraliza o ganho da repetição.** Replicado em teste:
   −1,75 pp vs real × 2, 12/12 comparações pareadas; ≈ real × 1.
2. **Nenhuma característica manipulada do crop (escala, contraste) altera
   esse quadro.** Escala: nula no teste. Contraste: nula em val e teste.
3. **Proxies de detectabilidade não predizem utilidade de treino.**
   Contraste, a feature mais forte do Estágio A, é nula no treino. A
   atribuição observacional (SHAP sobre acerto de um detector) mediu
   plausibilidade, não utilidade.
4. **O que ajuda é sinal real (ou mais passos sobre ele)**: real × 2
   supera real × 1 em +1,2 pp — confundido com o dobro de passos; a ser
   separado no próximo experimento (protocolo de passos fixos).
5. **Efeitos abaixo do piso de 2,0 pp não são confiáveis mesmo com
   direção consistente em 3 seeds** (P5b' em val vs teste): a regra
   pré-registrada funcionou como deveria.
6. **Vale reportar como limitação de método**: com crops de qualidade
   mínima (≥ 20 px), "ampliação" é fisicamente impossível para ~82% das
   caixas de um alvo de vigilância marítima; o regime discutido na
   literatura só existe para objetos grandes.

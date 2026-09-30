# Resultados da Fase 5 — composição sintética vs. real com passos igualados

Pré-registro: adendo 3 (`docs/pre_registro/adendo3_fase5_passos_igualados.md`,
commit `3004384`, tag `pre-registro-adendo3`). Análise fixada em `d1cb1a0`
(código idêntico ao patch gerado antes de qualquer métrica; ver o changelog
de 2026-09-29 sobre o cegamento). Resultados brutos:
`docs/fase5_resultados_val.json`.

## 1. O que foi testado

Na Fase 3, as células sintéticas receberam ~2× os passos de otimização do
controle (150 épocas com 5.288 contra 2.696 imagens por época). A Fase 5
igualou os passos: trainlist de comprimento fixo 5.392 em todos os braços,
fração sintética p ∈ {0; 0,25; 0,50} (C, M25, M50), dois orçamentos
(S1 = 10.110 passos, S2 = 25.275 passos), 5 seeds. São 30 execuções, todas
íntegras (G2 GO com pesos idênticos; auditorias S1 e S2 com 15/15 cada).

Métrica primária: recall no ponto de máximo-F1 na última época
(`results.csv`), split de validação (332 imagens, 1.267 caixas).

## 2. Médias por braço (validação, 5 seeds)

| Orçamento | Braço | Recall | mAP50 | Recall small | Área sob a curva |
|---|---|---|---|---|---|
| S1 | C   | 0,6873 | 0,7517 | 0,7004 | 0,6489 |
| S1 | M25 | 0,6789 | 0,7454 | 0,6974 | 0,6396 |
| S1 | M50 | 0,6546 | 0,7345 | 0,6796 | 0,6190 |
| S2 | C   | 0,6862 | 0,7472 | 0,7077 | 0,6658 |
| S2 | M25 | 0,6911 | 0,7515 | 0,7120 | 0,6583 |
| S2 | M50 | 0,6891 | 0,7476 | 0,7092 | 0,6500 |

## 3. Vereditos pela letra do adendo (§6.1, §6.5, §7)

Diferenças pareadas por seed em pontos percentuais; IC com t de Student, df = 4.

### F1 — confirmatória (Holm sobre P11, P12, P13)

| Contraste | Média | IC95 | Por seed | p Holm | Veredito |
|---|---|---|---|---|---|
| P11: M50 − C (S2) | +0,29 | [−1,41; +1,99] | +0,22, +0,95, −1,42, +2,17, −0,47 | 1,000 | **inconclusivo** (dp 1,37 pp > 0,8: subdimensionado) |
| P12: linear/2 (S2) | +0,14 | [−0,70; +0,99] | — | 1,000 | "equivalente" — **não interpretável** (ver 3.1) |
| P13: interação | +3,56 | [−0,87; +8,00] | +3,63, +6,54, −0,95, +7,51, +1,08 | 0,268 | **interação não detectada** (subdimensionado) |

**Consequência pré-registrada (§6.5) para P11 inconclusivo**: "P10
permanece com o confundimento declarado como limitação."

#### 3.1 P12 não deve ser lido como evidência

Com três doses equiespaçadas, o contraste linear (−1, 0, +1) dá peso zero a
M25: P12 = P11/2, com o mesmo t e o mesmo p. O veredito "equivalente" surge
apenas porque o valor dividido por 2 é comparado à mesma margem de ±1 pp.
É um erro de redação do adendo 3, registrado ANTES da análise (changelog de
2026-09-29). O contraste que captura a forma da dose-resposta é o quadrático
(F3c/F3d, exploratório).

### F2 — secundária (Holm dentro da família)

| Contraste | Média | IC95 | p Holm | Leitura |
|---|---|---|---|---|
| F2a: P11 no estrato small | +0,15 | [−0,57; +0,86] | 1,000 | equivalente (IC90 dentro de ±1 pp; TOST sem ajuste múltiplo, que o adendo não previu) |
| F2b: P11 em mAP50 | +0,04 | [−1,07; +1,15] | 1,000 | equivalente (mesma ressalva) |
| **F2c: P11 na área sob a curva** | **−1,57** | **[−1,94; −1,21]** | **0,001** | **sintético pior ao longo da trajetória; 5/5 seeds negativas** |
| F2d: M50 − C em S1 | −3,27 | [−6,08; −0,46] | 0,096 | **não significativo após Holm** |

Sobre F2d: o script atribui o rótulo "sintetico_pior" pelo IC95 não
ajustado. Pelo §7, as secundárias são corrigidas por Holm dentro da
família; com p de Holm = 0,096, a leitura correta é *não significativo após
correção*. Isso é a aplicação do §7, não uma mudança de regra.

### Análise complementar: ANOVA 2×3 com seed como bloco

Orçamento F(1,20) = 8,14, p = 0,010; fração F(2,20) = 3,13, p = 0,066;
interação F(2,20) = 3,81, p = 0,040; seed F(4,20) = 2,66, p = 0,062.
Complementar, sem correção; não substitui P13.

### F3 — exploratória (sem inferência confirmatória)

- F3a (M25 − M50, S2) = +0,20 pp; F3b (M25 − C, S2) = +0,49 pp; ambos com IC amplo.
- F3c (quadrático, S2) = −0,35 pp [−3,99; +3,30]; F3d (quadrático, S1) =
  −0,80 pp [−1,32; −0,28]: em S1, M25 fica acima da reta entre C e M50, ou
  seja, a perda cresce mais que linearmente com a dose.
- Passo do pico (média das seeds): S1 C 9.301, M25 9.301, M50 8.762; S2 C
  19.074, M25 20.894, M50 20.422. **Com passos igualados, os braços
  sintéticos não atingem o pico mais cedo.**
- Sanidade (não pareada): C(S2) = 0,6862 contra o controle da Fase 3 =
  0,7051 (−1,89 pp) com quase o mesmo número de passos (25.275 contra
  25.350), mas estrutura de época diferente (real × 4 em 75 épocas contra
  real × 2 em 150 épocas; close_mosaic 5 contra 10 épocas).

## 4. Leitura substantiva

Cada afirmação traz o seu estatuto.

1. **[Confirmatório]** Com passos igualados, a diferença no recall final
   entre 50% de sintético e real puro é +0,3 pp (IC95 −1,4 a +2,0). Não há
   evidência de que o sintético melhore, nem de que piore. Também não foi
   possível afirmar equivalência (o experimento ficou subdimensionado para
   a margem de ±1 pp).
2. **[Post hoc]** A desvantagem da Fase 3 (−1,75 a −1,80 pp) fica, por
   pouco, abaixo do limite inferior do IC95 de P11 (−1,41). Isso é
   compatível com a hipótese de que ela era efeito do dobro de passos, mas
   não a prova, e não era critério pré-registrado.
3. **[Secundário, robusto]** Ao longo do treino, o braço com 50% de
   sintético rende menos que o real puro (−1,57 pp na área sob a curva,
   5/5 seeds, p de Holm = 0,001). A diferença se fecha no fim do orçamento
   S2.
4. **[Sugestivo, não confirmado]** No orçamento curto (S1), o sintético
   parece pior (F2d, −3,27 pp, não sobrevive ao Holm), e a interação vai
   na direção prevista (P13 +3,56 pp, não detectada; ANOVA p = 0,040 sem
   correção). Hipótese para testar: *o sintético é menos eficiente por
   passo, e o custo diminui quando há passos suficientes*.
5. **[Exploratório]** A leitura "a composição acelera o sobreajuste"
   (Fase 3, suspensa no adendo 3) não encontra apoio: com passos
   igualados, o pico dos braços sintéticos não vem antes.

### Reformulação da conclusão da Fase 3

> Com passos de otimização igualados, não há evidência de que a composição
> sintética melhore o recall final no CITRA-3D-Real (M50 − C = +0,3 pp,
> IC95 −1,4 a +2,0; 5 seeds). A desvantagem de ~1,8 pp observada na Fase 3
> não se reproduziu, e o experimento não teve precisão para afirmar
> equivalência. Ao longo do treino, o sintético rendeu consistentemente
> menos (−1,6 pp na área sob a curva, 5/5 seeds).

## 5. Lições de método

- **A última época é um endpoint ruidoso**: dp das diferenças pareadas de
  1,37 pp no recall final, contra 0,29 pp na área sob a curva. No braço C
  do S2, o recall final vai de 0,660 a 0,718 entre seeds. Em experimentos
  futuros, a primária deveria ser a área sob a curva ou a média das últimas
  k épocas, e o dimensionamento deveria usar a variância do endpoint
  escolhido.
- **Contrastes lacrados precisam ser verificados quanto a redundância**
  (P12 = P11/2), como já havia acontecido com o P6' do adendo 2.
- **Um veredito por IC não ajustado precisa respeitar a família**: o
  script deveria aplicar a regra §6.1 sobre ICs corrigidos em F2. Fica
  registrado como limitação do código, sem alterar o que foi lacrado.

## 6. Teste (adendo 3 §9)

*A preencher após a avaliação única com `scripts/avaliar_teste_fase5.py`.
Critério: P11 "replica" se o veredito no teste cair na mesma categoria de
§6.1 que na validação. F2c não é calculável no teste (só `last.pt` foi
salvo).*

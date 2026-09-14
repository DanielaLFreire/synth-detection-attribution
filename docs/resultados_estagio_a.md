# Resultados do Estágio A — confronto com o pré-registro

Data de fechamento: 2026-09-14.
O arquivo de previsões (`pre_registro/previsoes_fase0.md`) está lacrado por
hash (`pre_registro/hashes.json`) e não foi alterado. Este documento é o
confronto: uma linha por previsão, veredito pela LETRA do critério, e a
leitura substantiva separada — nunca misturadas.

## Vereditos pela letra do critério pré-registrado

| Previsão | Critério de confirmação | Resultado | Veredito |
|---|---|---|---|
| P1a — `fator_reescala` no top 3 | fora do top 8 = refutação | posição 9,4 ± 1,0 (total), 0% top-5 | **Refutada** |
| P1b — `novidade_pool` no top 3 | fora do top 8 = refutação | 12ª/14 (total); 9,7 ± 0,5 (controlado) | **Refutada** |
| P1c — `coerencia_escala_pos` no top 3 | — | r = 1,0000 com log(área): degenerada neste domínio | **Não testável** (sem gradiente de perspectiva no CITRA) |
| P2 — `dist_clip_alvo` fora do top 5 | dentro do top 3 = refutação | 14ª/14 (total, enquadramento original) | **Confirmada** |
| P3 — fonte mediada por escala + folga (queda ≥ 70%) | queda < 30% = refutação | queda 58,2% (mediadoras de P3); 93,9% (todas as de crop) | **Não confirmada** (58% < 70%) |
| P4 — volume do pool fora do top 8 | dentro do top 3 = refutação | nenhuma feature de volume no modelo | **Satisfeita por construção**, não empiricamente |

P5–P7 pertencem às Fases 3 e 4 e permanecem abertas.

## Leitura substantiva (separada dos vereditos)

1. **Geometria herdada domina o alvo.** 57,8% da variância do acerto é
   entre grupos (tamanho/posição da caixa real); 42,2% é efeito de
   composição. O modelo total é dominado pela geometria; a análise
   controlada por grupo (taxa leave-one-out) isola o efeito de composição.
2. **O efeito de escala existe, é não-monotônico e assimétrico.**
   Dependência parcial de `log_fator_reescala` em U invertido: pico em
   escala casada (log ∈ [−1, +0,5], SHAP +0,18); ampliação extrema
   (fator > 20×) custa **−0,53**, redução extrema (< 0,05×) apenas −0,08.
   A operacionalização pré-registrada (log com sinal, ranking linear) era
   cega a esse formato. Achado exploratório → hipótese confirmatória para
   P5 (Fase 3), com refinamento sugerido: separar "descasada por redução"
   de "descasada por ampliação".
3. **Resolução nativa e fotometria são os determinantes dominantes no
   nível do crop.** `contraste` (1º entre as de crop em 100% das
   reamostras), `crop_menor_lado_original_px` (2º), `brilho_medio` (−).
   `nitidez` (Laplaciano) quase não importa: a resolução de origem carrega
   a informação, não a textura de alta frequência.
4. **Fonte não tem efeito próprio.** 94% da importância de `fonte`
   desaparece com as propriedades do crop medidas — mas via resolução
   nativa e fotometria, não via escala/folga como P3 previa.
5. **Aparência semântica (CLIP) não adiciona nada.** Ganho preditivo
   −0,0003. `dist_clip_alvo` é colinear com escala/resolução (|r| > 0,7);
   `novidade_pool` é irrelevante para detectabilidade.
6. **Padrão transversal.** As previsões que erraram, erraram na mesma
   direção: superestimamos descasamento de escala e semelhança de
   domínio; subestimamos resolução nativa e fotometria. É uma história
   coerente, mais interessante que a prevista — e o pré-registro é o
   que garante que ela é legítima, não ajustada ao resultado.

## Números-chave

| Modelo | AUC-PR | AUC-ROC |
|---|---|---|
| Total, 13 features (portão pré-registrado ≥ 0,78) | 0,857 | 0,753 |
| Controlado, só covariável de grupo | 0,941 | 0,905 |
| Controlado, + 7 features de crop | 0,962 | 0,927 |
| Controlado, + CLIP | 0,962 | 0,927 |

Taxa base do alvo: 0,702. Alvo: votação majoritária de 3 checkpoints de
B2 (época 150), IoU ≥ 0,5, confiança ≥ 0,25.

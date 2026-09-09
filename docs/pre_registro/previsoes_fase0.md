# Previsões pré-registradas — Fase 0

*Commitado antes de qualquer resultado do Estágio A ou B. Cada previsão é
específica e falseável — o critério de confirmação/refutação está declarado
junto com cada uma, para que não haja espaço de reinterpretação posterior.*

*Este documento, uma vez commitado num repositório público, carrega um
carimbo de tempo verificável por terceiros (§0 do plano) — é essa
verificabilidade externa que dá valor de pré-registro a este texto, não a
promessa de honestidade da equipe.*

---

## 1. Contexto: o que já sabemos antes de prever

Antes de prever, listamos o que já é **fato medido**, não hipótese — para
não confundir, mais tarde, o que era conhecido antes do Estágio A rodar com
o que só o Estágio A revelou:

- Perfil do alvo (CITRA-3D-Real, tarefa 0.1): 82,2% dos objetos são "small"
  (COCO@640, método letterbox), mediana de área ~0,1% da imagem.
- Perfil das quatro fontes (tarefa 0.2): tamanho nativo mediano — SMD 54px,
  SeaShips 73px, ABOShips 27px, InaTechShips 358px (mediana do menor lado).
- Cobertura do reservatório para o fator escala (tarefa 0.3): InaTechShips
  incompatível de escala com o alvo (0,75% de pareamentos "casados" contra
  18–23% das outras três) — excluído da célula "escala casada" do fatorial.
- Padrão de folga de anotação observado no SeaShips (inspeção de qualidade
  da segmentação, 2026-09-02): várias caixas originais abrangem mais de um
  objeto, com água vazia entre eles.
- ABOShips tem 38,3% dos crops com menor lado <20px — fração de objetos
  minúsculos muito maior que as outras três fontes.

Essas quatro observações **já aconteceram** e alimentam as previsões abaixo
— não são previsões em si, são o ponto de partida.

---

## 2. Previsões para o Estágio A (ranking SHAP)

### P1 — Ranking de importância

**Previsão**: as três features de maior importância no SHAP, em ordem, serão:
1. `fator_reescala` (ou a feature de escala equivalente que sobreviver à
   checagem de multicolinearidade, §5.5 do plano)
2. Uma medida de diversidade/novidade do pool (`novidade_pool` ou
   equivalente)
3. Uma feature de coerência espacial (`coerencia_escala_pos` ou
   equivalente)

**Critério de confirmação**: essas três (ou os clusters que as contêm,
após checagem de multicolinearidade) aparecem entre as 5 primeiras posições
do ranking SHAP, com sinal estável sob bootstrap (§9, Fase 2).

**Critério de refutação**: qualquer uma delas cair fora do top 8, ou o
sinal não ser estável sob bootstrap.

### P2 — Similaridade CLIP ao alvo não é preditor forte

**Previsão**: `dist_clip_alvo` (distância CLIP ao perfil do alvo) fica fora
do top 5 do ranking SHAP — consistente com o achado já estabelecido do
artigo original (CLIP não prediz transferência).

**Critério de confirmação**: `dist_clip_alvo` fica abaixo da 5ª posição.

**Critério de refutação**: `dist_clip_alvo` aparece no top 3.

### P3 — "Fonte" é mediada por `fator_reescala` e `folga_anotacao`

**Previsão específica, derivada dos achados de 2026-09-02**: se "fonte"
(como variável categórica) aparecer com importância alta no SHAP antes de
`fator_reescala` e `folga_anotacao` serem incluídas, essa importância cai
para próxima de zero depois de incluí-las — porque a diferença aparente
entre fontes é explicada por essas duas variáveis (o InaTechShips difere
por escala nativa; o SeaShips difere por folga de anotação), não por
"fonte" ser uma causa própria e independente.

**Critério de confirmação**: teste de mediação (§6 do plano) mostra queda
de pelo menos 70% na importância de "fonte" após incluir `fator_reescala`
e `folga_anotacao`.

**Critério de refutação**: "fonte" mantém importância alta mesmo após
incluir as duas variáveis mediadoras — indicaria um efeito de fonte
genuíno, não capturado pelas features já especificadas, e exigiria revisão
da Família de features.

### P4 — Volume do pool não é preditor

**Previsão**: nenhuma medida de volume/tamanho do pool de origem aparece
no top 8 — consistente com o achado já estabelecido do artigo original
(volume 16K→32K foi nulo).

**Critério de confirmação/refutação**: análogo a P2.

---

## 3. Previsões para o Estágio B (fatorial de confirmação)

### P5 — Efeito principal de "escala casada" positivo e acima do piso de ruído

**Previsão**: o braço com escala casada supera o braço com escala descasada
em recall in-domain, com efeito acima do piso de ruído a ser medido na
piloto (Fase 1) — direção do efeito prevista, magnitude não (será medida).

**Critério de confirmação**: delta médio positivo, consistente entre
seeds, acima do piso de ruído.

**Critério de refutação**: delta não distinguível do piso de ruído, ou
direção invertida (escala descasada supera escala casada).

### P6 — Assimetria de fonte na célula "escala casada" não distorce o efeito

**Previsão**: mesmo com o InaTechShips excluído da célula "escala casada"
(decisão da tarefa 0.3), o efeito principal de escala continua
interpretável — porque as três fontes remanescentes (SMD, SeaShips,
ABOShips) têm reservatório comparável entre si para essa célula.

**Critério de confirmação**: nenhum indício de que o efeito de escala seja
inteiramente atribuível a uma única fonte dominante dentro da célula
"casada" (checagem: efeito de escala permanece na mesma direção quando
analisado fonte a fonte, dentro da célula).

---

## 4. Previsão para a validação de generalização (Fase 2.5, UA-DETRAC)

### P7 — O mecanismo de escala se replica, a magnitude não precisa

**Previsão**: no Estágio A replicado sobre o UA-DETRAC, `fator_reescala`
(ou equivalente) também aparece entre as 3 features de maior importância —
mesmo mecanismo do domínio marítimo, mesmo que a magnitude do efeito e o
ranking exato das demais features difira (dado que a estrutura de
dificuldade já se mostrou distinta entre os dois domínios — objeto
minúsculo isolado no SMD vs. oclusão por densidade no UA-DETRAC).

**Critério de confirmação**: `fator_reescala` no top 5 do ranking SHAP do
UA-DETRAC.

**Critério de refutação**: `fator_reescala` fora do top 8 no UA-DETRAC —
indicaria que o mecanismo é específico do domínio marítimo, não geral.

---

## 5. O que este documento não prevê (deliberadamente)

Consistente com os limites já declarados no plano (§11): não prevemos
ordenação fina entre fontes abaixo do piso de ruído, não prevemos que os
resultados generalizem além de detecção de objeto único em domínios
estruturalmente análogos aos validados, e não tratamos o Estágio A isolado
como evidência causal — só A+B juntos sustentam as previsões de causa
(P1–P4 são sobre associação observacional; P5–P6 são as únicas que testam
causalidade de verdade).

---

*Registrado para commit em 2026-09-02. Hash deste arquivo e timestamp do
commit git servem como evidência externa de que estas previsões foram
escritas antes de qualquer execução do Estágio A ou B.*

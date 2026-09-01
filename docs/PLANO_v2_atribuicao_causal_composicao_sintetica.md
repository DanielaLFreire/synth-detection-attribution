# PLANO — Atribuição Causal de Características em Composição Sintética de Dados para Detecção de Embarcações

*Versão 2. Documento de pré-registro de um projeto **novo e independente** — não é
extensão do artigo SIBGRAPI nem do repositório `maritime-crossdomain`. Reaproveita
lições metodológicas desse trabalho anterior (citadas onde relevante), mas com
repositório, baseline, pipeline e pré-registro próprios.*

*Status: RASCROSSO → torna-se pré-registro quando as condições da Fase 0 (§9)
forem satisfeitas e o commit de previsões for lacrado. Nenhuma execução de GPU
precede esse commit.*

*Objetivo editorial declarado: periódico topo do percentil da área (Qualis
Referência / Scimago Q1). Isso muda requisitos em relação a um artigo de
conferência — ver §2.*

---

## 0. O que mudou em relação ao plano anterior

Esta versão incorpora oito correções discutidas e verificadas contra o código
real do projeto anterior (`maritime-crossdomain`), não apenas por argumento
teórico:

| # | Problema identificado | Correção incorporada |
|---|---|---|
| 1 | Vazamento de grupo: colagens da mesma `(imagem, caixa)` repetem geometria idêntica em até 13 variações | Estágio A modelado com agrupamento por `(imagem, caixa)`; split treino/teste do modelo substituto por grupo, nunca por colagem individual (§5.1) |
| 2 | Confound de memorização de cena: gerar colagens de sondagem sobre fundos de TREINO reintroduz viés de gradiente já visto pelos modelos usados para rotular "acerto" | Colagens de sondagem do Estágio A geradas sobre o split de **validação**, nunca sobre o de treino (§5.2) |
| 3 | `compose_inplace` do projeto anterior não grava nenhum metadado por colagem — o "manifesto" não existe, precisa ser escrito do zero | Especificação de engenharia explícita do manifesto, como entregável de Fase -1, não um ajuste incidental (§5.3) |
| 4 | Multicolinearidade entre features de escala pode distorcer SHAP | VIF/correlação reportados antes do SHAP; features colineares agrupadas em clusters para interpretação (§5.5) |
| 5 | Nenhum piso de desempenho preditivo exigido do modelo substituto antes de confiar no SHAP | Portão de AUC-PR mínimo, medido em split por grupo, antes de interpretar o ranking (§5.4) |
| 6 | Alvo binário do Estágio A gerado por um único checkpoint/seed pode herdar idiossincrasia (lição já conhecida do seed 42) | Alvo agregado por votação sobre múltiplos checkpoints/seeds (§5.6) |
| 7 | `interp` listada como feature observacional mas hoje é constante (LANCZOS fixo) no código-fonte original | Removida do Estágio A observacional; só entra como fator manipulado do Estágio B, se o grupo decidir testá-la (§6) |
| 8 | Fatorial fracionado sem declarar resolução/confundimento de interações | Resolução do design declarada explicitamente; proporção de fontes balanceada entre células (§5.7) |

Além disso, esta versão adiciona dois requisitos novos, motivados pelo objetivo
de publicação em periódico Q1 (não presentes no plano anterior, que mirava
conferência):

- **§2.3** — plano de validação leve de generalização em um segundo domínio-alvo.
- **§2.4** — decisão de disponibilidade de dados como artefato de Fase 0, não
  como pendência de submissão.

---

## 1. Pergunta de pesquisa

> Dado um dataset-alvo operacional com perfil estrutural medido, **quais
> características dos crops, das fontes e do processo de composição
> determinam causalmente** a qualidade de um dataset sintético montado a
> partir de fontes públicas, para detecção de um objeto de interesse — e quais
> características plausíveis **não** determinam?

A pergunta é de **atribuição causal**, não de otimização. Um método de
composição, se emergir, é subproduto, não o objetivo.

## 2. Posicionamento editorial

### 2.1 Enquadramento do artigo

O artigo deve ser posicionado como uma **contribuição metodológica/protocolar**
— um procedimento de atribuição causal (descoberta barata + confirmação
fatorial) para composição sintética, validado com um estudo de caso
operacional completo — e não como "encontramos um método melhor de aumentar
dados". Isso importa porque os efeitos absolutos são pequenos (frações de
ponto percentual de recall, décimos acima do piso de ruído medido). Sob o
enquadramento errado, isso lê como fraco; sob o enquadramento correto (rigor
como o produto), é exatamente o ponto forte do artigo.

### 2.2 Família de periódicos alvo

Não mirar diretamente os três generalistas de topo de visão computacional
(TPAMI/IJCV/CVIU) como primeira tentativa — eles cobram generalidade ampla
(múltiplos domínios/classes, contribuição algorítmica nova), e este projeto se
declara honestamente restrito a detecção de um objeto de interesse em um
domínio operacional específico. Alvo mais realista, ainda Q1/topo de percentil:
periódicos de domínio aplicado com tradição empírica forte (ex.: sensoriamento
remoto/vigilância, reconhecimento de padrões aplicado, sistemas inteligentes).
A escolha final do periódico deve ser feita perto da submissão, com base no
scope exato e no volume de resultados obtidos — não é necessário travá-la
agora.

### 2.3 Requisito de generalização (novo)

Incluir, como parte do escopo (não como "trabalho futuro"), uma réplica
**barata** do Estágio A (sem GPU de treino, só inferência com modelos já
existentes ou um substituto público) em um **segundo dataset-alvo** de objeto
pequeno/denso, estruturalmente análogo ao alvo operacional. Objetivo: mostrar
que o ranking de features (compatibilidade de escala > diversidade > coerência
espacial > similaridade visual) não é uma peculiaridade de um único dataset.
Isso é uma fase leve (semanas, não meses) e fortalece substancialmente o
argumento de generalidade perante revisores de periódico.

**Decisão registrada: segundo dataset-alvo = UA-DETRAC.** Justificativa: o
objetivo desta validação é isolar o efeito de *domínio de conteúdo* do efeito
de *estrutura de captura* — trocar o domínio (mar → tráfego) mantendo o
estilo estrutural o mais próximo possível do alvo primário (câmera fixa de
vigilância, objeto pequeno e distante, cena densa, classe colapsável a
única). O UA-DETRAC atende a isso: 100 vídeos de câmera fixa em 24 locais,
~140 mil frames, 1,21 milhão de caixas anotadas, com escala do veículo já
categorizada pelos próprios autores em três faixas por raiz da área (pequeno
0–50 px, médio 50–150 px, grande >150 px) — o que reduz o trabalho de
perfilamento estrutural da Fase 0. As quatro subclasses de veículo
(carro/ônibus/van/outro) são colapsadas para uma única classe `vehicle`,
espelhando o tratamento de classe única já usado no alvo primário
(`vessel`). Uma alegação de generalidade "o mecanismo se replica quando o
domínio muda mas a estrutura da cena se mantém" é defensável sem prometer
generalidade universal — e é mais fácil de sustentar perante um revisor do
que uma mudança simultânea de domínio e modalidade de captura.

**Alternativa documentada (não descartada): VisDrone2019-DET.** Câmera
aérea/UAV, 68% dos objetos com menos de 32×32 px, 10 classes colapsáveis a
`vehicle` ou `pessoa`. Muda domínio **e** modalidade de captura (aéreo móvel
vs. fixo) simultaneamente — alegação de generalidade mais ambiciosa, porém
mais difícil de interpretar se o ranking não se replicar (não dá para
separar se a discrepância vem do mecanismo ou da modalidade). Fica como
extensão possível da Fase 2.5 se houver tempo/orçamento, não como
substituto do UA-DETRAC.

**Descartado para este projeto (não para a linha de pesquisa): SeaDronesSee.**
Ainda é domínio marítimo — testaria generalidade de *sensor* (drone vs.
câmera fixa), não de *domínio*, que é uma pergunta diferente da que o §2.3
propõe. Registrado como candidato a um terceiro domínio de validação em
trabalho de seguimento.

### 2.4 Disponibilidade de dados (novo, decidir na Fase 0)

Se o dataset-alvo operacional tiver restrição de compartilhamento (origem
institucional/operacional), isso precisa ser resolvido **antes** da Fase 2, não
na hora de submeter — periódicos Q1 exigem declaração de disponibilidade de
dados e cada vez mais pedem reprodutibilidade verificável. Opções a decidir na
Fase 0: (a) liberar uma amostra anonimizada; (b) obter carta formal de exceção
de sigilo aceita pela revista; (c) publicar o framework/protocolo com um
dataset público equivalente como demonstração de reprodutibilidade, mantendo o
dataset operacional como estudo de caso restrito. A decisão entra no commit de
pré-registro da Fase 0.

## 3. Tese

> Dado um alvo operacional, as características que determinam o ganho de um
> dataset sintético composto a partir de fontes públicas podem ser
> **descobertas** por atribuição barata no nível da colagem (Estágio A,
> corrigida por agrupamento geométrico) e **confirmadas** por manipulação
> fatorial controlada (Estágio B). Preveem-se como determinantes: compatibilidade
> de escala, diversidade de aparência do pool e coerência espacial da
> colagem. Preveem-se como não-determinantes, exceto como proxies de outra
> coisa: similaridade visual global ao alvo (CLIP), volume do pool, e
> identidade da fonte (exceto na medida em que "fonte" seja proxy de
> qualidade de anotação — hipótese testada explicitamente).

Cada oração é falsificável e será registrada em commit ao fim da Fase 0.

## 4. Baseline

Baseline operacional: fine-tuning direto de pesos pré-treinados (COCO ou
equivalente) no split de treino do dataset-alvo. Protocolo de treino fechado
e versionado **neste** repositório (não herdado tacitamente do projeto
anterior): épocas fixas, `patience=0` (schedule completa), warmup igualado em
steps (não em épocas — evita o erro de comparação já documentado na literatura
interna do grupo, onde `warmup_bias_lr` diferente invalidou uma comparação),
cache em disco, checkpoint selecionado por época pré-registrada — nunca por
métrica de validação, porque a validação (tipicamente pequena) não prevê
ordenação no teste de forma confiável.

## 5. Desenho experimental em dois estágios (versão corrigida)

### 5.1 Unidade de análise e estrutura de agrupamento

A unidade nominal continua sendo **a colagem** (crop × caixa destino × imagem
composta), mas com uma correção estrutural: se a composição herdar posições de
caixas reais do dataset-alvo (como no processo verificado no projeto anterior),
a geometria (posição, área da caixa) é constante para todas as variações da
mesma caixa. Portanto:

- Toda modelagem estatística do Estágio A (GBM, SHAP, bootstrap) usa
  **agrupamento por `(imagem, caixa)`** como unidade de validação cruzada —
  nunca split aleatório por colagem individual.
- Features geométricas (posição, área da caixa, coerência escala×posição) são
  reportadas com o número real de configurações geométricas independentes, não
  com a contagem de colagens.
- O relatório do Estágio A declara explicitamente essa distinção (N de
  colagens vs. N de grupos geométricos independentes).

### 5.2 Geração das colagens de sondagem — sobre o split de validação

Para evitar o confound de memorização de cena (um detector já treinado por
gradiente sobre um fundo específico "acerta" por familiaridade da cena, não
pela qualidade da colagem), as colagens usadas para gerar o alvo binário do
Estágio A são compostas **sobre o split de validação** do dataset-alvo, nunca
sobre o de treino. Justificativa: imagens de validação não recebem
atualização de peso por *backprop* durante o treino (só entram no cálculo da
métrica de parada), portanto o viés de memorização de pixel é muito menor ali.
Essa escolha é registrada explicitamente no pré-registro.

**Nota sobre um viés residual considerado e descartado**: usar o split de val
para gerar as colagens de sondagem não compromete a separação
observação→confirmação do desenho (§5), porque a métrica de decisão causal do
Estágio B é lida no split de **teste** — nunca tocado pelo Estágio A. A única
forma de contaminação que precisaria de atenção seria indireta: se o
checkpoint usado para gerar o alvo binário do Estágio A fosse escolhido *por
desempenho no val* (early stopping clássico), esse checkpoint estaria, em
grau pequeno, favorecido para ir bem justamente nesses fundos — um viés
uniforme sobre a taxa de acerto, não diferencial entre features, mas evitável.
**Esse viés não se aplica aqui**: o protocolo de treino V2 (§3) já especifica
que o checkpoint é selecionado por **época pré-registrada fixa**, nunca por
métrica de validação — logo, nenhuma seleção informada pelo val ocorre em
nenhum ponto da cadeia. A decisão de época fixa foi tomada por outro motivo
(instabilidade de seleção por val em conjuntos pequenos) mas fecha, como
efeito colateral, esta lacuna também.

### 5.3 Manifesto de composição — especificação de engenharia

O componente de composição sintética deste projeto (escrito do zero neste
repositório, não herdado) deve gravar, por colagem, no mínimo:

- id do crop utilizado e sua fonte;
- imagem-alvo e id da caixa de destino;
- dimensões da caixa de destino e área original do crop (permite computar
  `fator_reescala` sem reprocessamento);
- método de interpolação usado (mesmo que fixo — registrar explicitamente o
  valor constante, não deixar implícito);
- seed do sorteio daquela colagem específica.

Este manifesto é pré-requisito absoluto do Estágio A (nenhuma feature da
família de transformação pode ser computada sem ele) e deve ser tratado como
tarefa de engenharia própria na Fase -1, com testes automatizados de
integridade (nenhuma colagem sem entrada correspondente no manifesto).

### 5.4 Modelo de importância — validação antes de interpretar

Modelo: gradient boosting + SHAP, como antes. Correção: antes de reportar
qualquer ranking, o modelo precisa passar por um portão de desempenho
preditivo — AUC-PR (dado o desbalanceamento esperado entre acerto/erro por
caixa) medido em validação cruzada **por grupo** (§5.1), com piso mínimo
definido no pré-registro. Um ranking "estável sob bootstrap" vindo de um
modelo com poder preditivo baixo é ranking estável de ruído, não evidência.

### 5.5 Tratamento de multicolinearidade

Antes do SHAP: reportar matriz de correlação/VIF entre as features candidatas,
com atenção especial ao cluster de escala (`fator_reescala`, `res_efetiva`,
`pct_escala_alvo`, `upsample`). Features com colinearidade alta são agrupadas
em clusters para fins de interpretação do ranking (importância do cluster, não
de cada membro isoladamente) — segue a prática documentada na literatura de
interpretabilidade para SHAP com features correlacionadas, evitando
redistribuição espúria de importância entre variáveis dependentes.

### 5.6 Robustez do alvo do Estágio A

O alvo binário (acerto/erro por caixa, IoU ≥ 0,5) não é gerado por um único
checkpoint. É agregado (ex.: votação majoritária, ou probabilidade média) sobre
múltiplos checkpoints/seeds de um mesmo braço de treino, para não herdar a
idiossincrasia de um seed específico no próprio alvo do modelo — o mesmo
cuidado que já se pratica na leitura de resultados finais (leave-one-seed-out)
se estende à geração do rótulo de entrada.

**Alternativa por aprendizagem em grupos**: antes de adotar o proxy de
poucas épocas de treino como substituto do desempenho convergido, validar em
piloto pequeno que o ranking de grupos a poucas épocas correlaciona com o
ranking final observado em braços já concluídos — não assumir a validade desse
atalho sem essa checagem.

### 5.7 Estágio B — fatorial de confirmação

As 3–4 features (ou clusters de features) do topo do Estágio A tornam-se
fatores manipulados de um desenho fatorial 2^k, com:

- **N de crops fixo entre células**;
- se o desenho for fracionado (2^(k−1) ou menor), a **relação definidora e a
  resolução do design são declaradas explicitamente no pré-registro**, com a
  lista de quais interações de segunda ordem ficam confundidas com quais
  efeitos principais;
- **proporção de cada fonte constante entre células** — verificada como
  condição de cobertura do reservatório na Fase 0, não apenas checada
  qualitativamente; sem isso, o fator manipulado pode voltar a se confundir
  com identidade da fonte, o mesmo problema que o desenho pretende eliminar;
- controle extra obrigatório: braço com o real sobreamostrado (mesmo fator de
  repetição do braço sintético) e **zero** sintéticos, isolando o efeito da
  repetição do real do efeito da composição em si.

Análise: ANOVA fatorial sobre a métrica primária, com **effect size
padronizado** (ex. d de Cohen pareado) reportado ao lado do delta bruto —
permite comparação entre este estudo e trabalhos futuros com pisos de ruído
diferentes, e é o tipo de rigor que revisores de periódico topo esperam além
de p-valor e IC.

## 6. Tabela de features do Estágio A (revisada)

Estrutura mantida em quatro famílias (intrínsecas do crop, de transformação,
espaciais/geométricas, relacionais ao alvo), com duas alterações:

- **`interp` removida da lista observacional.** Se o processo de composição
  usar um único método de interpolação fixo, não há variância a explicar; a
  feature só reaparece se o Estágio B decidir manipulá-la deliberadamente como
  fator (exigindo suporte a múltiplos métodos no pipeline de composição).
- **Features geométricas da Família 3** (`pos_v`, `pos_h`, `area_caixa`,
  `coerencia_escala_pos`) documentadas com a ressalva de agrupamento (§5.1):
  são propriedades de `(imagem, caixa)`, repetidas por construção em todas as
  variações daquela caixa, e reportadas com o N de configurações
  independentes, não o N de colagens.

As demais features seguem a especificação já validada no plano original
(intrínsecas medidas no crop original, nunca em resize canônico; features de
transformação como tratamento, não pré-processamento; decomposição de
"qualidade de anotação da fonte" via `folga_anotacao`/`truncamento`, com teste
de mediação para "fonte" pré-especificado).

## 7. Métricas e estatística

- Primária: recall in-domain no split de teste do dataset-alvo (nunca tocado
  antes da Fase 4).
- Secundária: mAP50 in-domain.
- Dimensionamento por análise de poder, com σ a medir na piloto (Fase 1) —
  não convencionado a priori.
- Bateria: t pareado por seed + IC-95% (primário); Wilcoxon (robustez);
  **effect size padronizado (d de Cohen pareado)** ao lado de cada delta;
  Holm–Bonferroni por família de comparações, com a **árvore de hipóteses
  completa declarada no pré-registro** antes de qualquer teste (quantas
  comparações por família, em que ordem);
  ANOVA fatorial para o Estágio B; leave-one-seed-out de rotina.
- Regra de leitura: um efeito só é reportado como real se a média superar o
  piso de ruído medido na Fase 1 **e** o sinal for consistente entre seeds.
  Sempre reportar deltas por seed, nunca só a média.

## 8. Pré-requisitos de pipeline (Fase -1, antes de qualquer medição)

1. **Repositório novo**, com pipeline de composição escrito para já emitir o
   manifesto por colagem (§5.3) — não uma adaptação incremental de código
   antigo, um componente novo com testes de integridade desde o commit
   inicial.
2. **Filtro de crop unificado** entre todas as fontes públicas usadas,
   registrado em manifesto de extração com hash — evita o confound já
   documentado na literatura interna do grupo entre "fonte" e "critério de
   filtro".
3. **Labels do dataset-alvo materializados** como artefato versionado único
   (`labels_final/`), gerados por um script único e auditável — não gerados em
   runtime a cada sessão.
4. **Protocolo de treino fechado e versionado** neste repositório (épocas
   fixas, warmup em steps, cache em disco, seleção de checkpoint por época
   pré-registrada).
5. **Extração de crops SAM (ou segmentador equivalente) de todas as fontes**
   planejadas, com o mesmo filtro do item 2.
6. **Decisão de disponibilidade de dados** (§2.4) registrada por escrito.
7. **Escolha do segundo dataset-alvo** para a validação leve de generalização
   (§2.3), com justificativa de similaridade estrutural ao alvo primário.

## 9. Fases e portões

**Fase -1 — Fundação e engenharia de pipeline.** Repositório novo, componente
de composição com manifesto, filtro unificado, materialização de labels,
protocolo de treino fechado, extração de crops das fontes públicas planejadas,
decisão de disponibilidade de dados. PORTÃO: os sete itens do §8 concluídos e
auditáveis por teste automatizado, antes de prosseguir.

**Fase 0 — Perfis e previsões (sem GPU).** Perfil estrutural do alvo; perfis
dos pools de fontes; verificação de que o reservatório cobre as células
pretendidas do fatorial **com proporção de fonte balanceada** (§5.7); geração
das colagens de sondagem sobre o split de validação (§5.2); escolha final do
segundo domínio de validação; **commit das previsões** (ranking esperado de
features, hipóteses específicas, decisão de dados). *Este commit é o coração
do artigo.*

**Fase 1 — Piloto do protocolo de treino (GPU).** Baseline + 1 braço de
composição + controle real-sobreamostrado, n=3 seeds. PORTÃO: determinismo
bit-a-bit (mesma seed duas vezes); medição do piso de ruído (duas larguras de
banda, reportar ambas).

**Fase 2 — Estágio A (GPU ~zero).** Rotulagem robusta do alvo binário
(múltiplos checkpoints/seeds, §5.6); construção da tabela de features a partir
do manifesto; checagem de multicolinearidade (§5.5); modelo GBM com split por
grupo e portão de AUC-PR (§5.4); SHAP com ranking, direções, interações de 2ª
ordem, estabilidade sob bootstrap. PORTÃO: desempenho preditivo do modelo
acima do piso pré-registrado **e** ranking estável sob bootstrap **e** ≥2
features (ou clusters) com sinal claro; senão, revisar o alvo do modelo.

**Fase 2.5 — Validação leve de generalização.** Repetição barata do Estágio A
no segundo dataset-alvo escolhido na Fase 0. Comparação qualitativa do ranking
de features entre os dois domínios.

**Fase 3 — Estágio B (fatorial, GPU).** Fatores = topo do Estágio A (ou
clusters). Resolução do design declarada; proporção de fonte balanceada por
célula; controle real-sobreamostrado sem sintéticos. Particionável por fator
se a cota de GPU faltar.

**Fase 4 — Síntese e redação.** Confronto entre previsões da Fase 0 e
resultados (previsões erradas são resultado publicável); preparação do
repositório de reprodutibilidade público; revisão interna de rigor antes da
submissão; escolha final do periódico-alvo (§2.2).

## 10. Riscos e mitigação

| Risco | Mitigação |
|---|---|
| Reservatório não cobre células do fatorial com fonte balanceada | Ajustar desenho na Fase 0 (reduzir k, ou aceitar desbalanceamento e reportar como limitação declarada, nunca oculta) |
| Alvo binário do Estágio A sem sinal (detector acerta quase sempre) | Alternativa por aprendizagem em grupos (§5.6), validada previamente por correlação de ranking |
| σ maior que o esperado na piloto | Redimensionar N por célula via análise de poder atualizada, antes do Estágio B |
| Cota de GPU insuficiente para o fatorial completo | Estágio B particionável — cada fator publicável isoladamente |
| Dataset operacional não liberável | Publicar framework com dataset público substituto; estudo de caso operacional como seção restrita ou apêndice |
| Segundo domínio de validação não disponível a tempo | Reportar Fase 2.5 como trabalho em andamento explícito, não bloqueia submissão do núcleo do artigo |

## 11. O que este projeto não promete

- Ordenação fina entre fontes abaixo do piso de ruído medido.
- Generalidade universal além de detecção de objeto único em domínios
  estruturalmente análogos ao(s) validado(s) — mitigada, não eliminada, pela
  validação leve de segundo domínio (§2.3).
- Causalidade a partir do Estágio A isolado — só Estágio A + B juntos
  sustentam uma afirmação causal.

## 12. Estrutura do novo repositório (proposta inicial)

```
<nome-do-projeto>/
├── configs/                     # parâmetros de datasets e protocolo
├── src/
│   ├── compose/                 # composição sintética COM manifesto por colagem (novo)
│   ├── profiling/                # perfil estrutural do alvo e das fontes
│   ├── attribution/              # Estágio A: features, GBM, SHAP, agrupamento
│   ├── factorial/                 # Estágio B: geração de células, ANOVA
│   └── train/                    # protocolo de treino fechado (V2 próprio)
├── scripts/                      # entry-points numerados, um por etapa de pipeline
├── docs/
│   ├── PLANO_v2_...md            # este documento
│   ├── preregistro/              # commit lacrado da Fase 0 (previsões, hashes)
│   └── CHANGELOG_metodologico.md # decisões registradas ao longo da execução
├── tests/                        # integridade do manifesto, determinismo, etc.
├── results/                      # CSVs consolidados, por fase
└── README.md
```

## 12.1 Organização do Google Drive (dados e artefatos não versionados)

O código vive no repositório novo (§12); imagens, crops, sintéticas, pesos de
modelo e resultados brutos — tudo pesado demais para Git — vivem no Drive.
Sem uma convenção explícita aqui, o projeto herda o mesmo tipo de confound já
documentado no projeto anterior (fontes extraídas com filtros diferentes,
zips sem hash, pastas soltas sujeitas a escrita parcial via FUSE).

**Decisão registrada: subpasta nova dentro da estrutura existente
(`PROJETO_MARINHA/`), não uma árvore de Drive isolada.** Reaproveita por
referência o que for dado-fonte imutável; regenera do zero o que carregar
viés de pipeline antigo.

### O que pode ser reaproveitado por referência (read-only, nunca duplicado)

- Datasets-fonte brutos como distribuídos originalmente: `ABOships.zip`,
  `seaship.zip`, `SeaShips_voc.zip`, `smd_clean.zip`, imagens brutas do
  `InaTechShips`, imagens e anotações originais do `CITRA-3D-Real`.
- Critério: são dados de terceiros ou o dataset operacional em seu estado
  bruto — nenhum deles carrega uma decisão de pipeline deste ou do projeto
  anterior, então reaproveitar é seguro e evita duplicar armazenamento.

### O que NÃO pode ser reaproveitado — precisa ser regenerado neste projeto

- **Crops já segmentados** (`crops_abo.zip`, `InaTechShips_crops_sam.zip`):
  foram extraídos com filtros inconsistentes entre fontes (MIN_DIM 20px +
  opacidade vs. MIN_DIM 50px sem opacidade — o confound documentado no
  changelog do projeto anterior). Reaproveitá-los reintroduziria exatamente o
  viés que o pré-requisito §8/item -1.3 existe para eliminar.
- **Qualquer `synth_*.zip` antigo**: gerado sem o manifesto por colagem
  exigido em §5.3 — sem o manifesto, as features da Família 2 não são
  reconstituíveis a partir dele.
- Ambos precisam ser recriados por este projeto, sob o filtro unificado e com
  o manifesto novo, mesmo que o *código* de extração seja inspirado no
  anterior.

### Estrutura proposta

```
PROJETO_MARINHA/                              # raiz existente, intocada
├── Datasets/                                 # fontes brutas — reaproveitadas por referência
│   ├── CITRA-3D-Real/
│   ├── InaTechShips/
│   └── _zips/                                # ABOships.zip, seaship.zip, SeaShips_voc.zip, smd_clean.zip
├── Experimento_CrossDomain/                  # projeto anterior — intocado, não usado aqui
└── EXPERIMENTO_ATRIBUICAO_CAUSAL/            # NOVO — tudo deste projeto
    ├── README_DRIVE.md                       # esta convenção, versão, o que é herdado vs. gerado
    ├── crops/                                # REGENERADOS sob filtro unificado (nunca os antigos)
    │   ├── _manifesto_extracao.json          # hash, parâmetros de filtro, data, fonte
    │   ├── crops_abo.zip
    │   ├── crops_inatech.zip
    │   ├── crops_smd.zip
    │   └── crops_seaships.zip
    ├── labels_final/                         # materializado e versionado (§8.4), não gerado em runtime
    ├── composicao/
    │   ├── manifesto_colagens/               # o manifesto por colagem (§5.3) — Parquet/CSV em lotes
    │   └── synth_*.zip
    ├── estagio_a/
    │   ├── colagens_sondagem_val/            # colagens geradas sobre o split de VALIDAÇÃO (§5.2)
    │   ├── features_table.parquet
    │   ├── shap_outputs/
    │   └── modelos_gbm/
    ├── estagio_b/
    │   ├── runs/                             # por célula do fatorial, por seed
    │   └── results_fatorial.csv
    ├── segundo_dominio_uadetrac/             # validação de generalização (§2.3)
    │   ├── fonte_ref.md                      # origem, hash, licença do UA-DETRAC
    │   ├── crops_veiculos/
    │   └── estagio_a_uadetrac/
    └── pre_registro/
        ├── commit_fase0.md                   # previsões lacradas
        └── hashes.json                       # hash de cada artefato citado no pré-registro
```

Convenções mantidas do projeto anterior por serem boas práticas verificadas:
zip único por artefato pesado (evita escrita arquivo-a-arquivo lenta e
vulnerável a queda via FUSE), manifesto com hash ao lado de cada zip gerado.
Nenhum artefato do Estágio A ou B é considerado válido para análise sem seu
manifesto correspondente presente.

## 13. Cronograma de atividades e tarefas

*Durações em semanas de trabalho efetivo, não semanas corridas — ajustar
conforme disponibilidade real da equipe e cota de GPU. Cada fase só inicia
quando o portão da fase anterior é satisfeito (§9); atrasos em uma fase
propagam, não são absorvidos silenciosamente.*

### Fase -1 — Fundação e engenharia de pipeline (estimado: 3 semanas)

| Tarefa | Descrição | Estimativa |
|---|---|---|
| -1.1 | Criar repositório novo, estrutura de pastas, licença, README inicial | 2 dias |
| -1.2 | Escrever componente de composição com manifesto por colagem (§5.3) + testes de integridade | 4–5 dias |
| -1.3 | Implementar filtro de crop unificado entre as fontes + manifesto de extração com hash (**re-extrair do zero — não reaproveitar `crops_abo.zip`/`InaTechShips_crops_sam.zip` do projeto anterior, que carregam filtros inconsistentes**, §12.1) | 2–3 dias |
| -1.4 | Materializar `labels_final/` do dataset-alvo, versionado, com script gerador auditável | 1–2 dias |
| -1.5 | Fechar protocolo de treino V2 (warmup em steps, épocas fixas, cache em disco) | 2–3 dias |
| -1.6 | Extrair crops (segmentação) das fontes públicas ainda não processadas | 1 dia GPU + 1 dia validação |
| -1.7 | Abrir processo de decisão de disponibilidade de dados (pode correr em paralelo, prazo administrativo variável) | iniciar imediatamente, paralelo às demais |
| -1.8 | Baixar UA-DETRAC, montar classe única `vehicle` (colapsar carro/ônibus/van/outro), preparar um banco de fontes de recorte de veículos para composição in-place análoga à do alvo primário | 3–4 dias |
| -1.9 | Criar `EXPERIMENTO_ATRIBUICAO_CAUSAL/` no Drive existente (§12.1), com a estrutura de pastas definida, `README_DRIVE.md` documentando o que é herdado por referência vs. regenerado, e conferir que nenhum crop/sintético antigo foi copiado por engano | 1 dia |

### Fase 0 — Perfis e pré-registro, sem GPU (estimado: 1,5–2 semanas)

| Tarefa | Descrição | Estimativa |
|---|---|---|
| 0.1 | Computar perfil estrutural do dataset-alvo (escala, aspecto, posição, centróide CLIP) | 1–2 dias |
| 0.2 | Computar perfis das fontes públicas | 1–2 dias |
| 0.3 | Verificar cobertura do reservatório para as células do fatorial, com proporção de fonte balanceada | 2 dias |
| 0.4 | Gerar colagens de sondagem sobre o split de validação (§5.2) | 1–2 dias |
| 0.5 | Redigir e commitar as previsões falsificáveis (ranking esperado, hipóteses, decisão de dados) | 2–3 dias |
| 0.6 | **Portão de fase**: lacrar o commit de pré-registro | — |

### Fase 1 — Piloto do protocolo de treino (estimado: 1 semana, GPU intensiva)

| Tarefa | Descrição | Estimativa |
|---|---|---|
| 1.1 | Rodar baseline + 1 braço de composição + controle real-sobreamostrado, n=3 seeds | 2–3 dias GPU |
| 1.2 | Verificar determinismo bit-a-bit (mesma seed, duas execuções) | 1 dia |
| 1.3 | Medir piso de ruído (duas larguras de banda) e reportar ambas | 1–2 dias análise |
| 1.4 | **Portão de fase**: determinismo confirmado e piso medido | — |

### Fase 2 — Estágio A (estimado: 2,5–3 semanas, GPU ~zero)

| Tarefa | Descrição | Estimativa |
|---|---|---|
| 2.1 | Rotular alvo binário por múltiplos checkpoints/seeds (agregação) | 2–3 dias |
| 2.2 | Construir tabela de features completa a partir do manifesto | 3–4 dias |
| 2.3 | Checar multicolinearidade (VIF/correlação) e definir clusters de features | 1–2 dias |
| 2.4 | Treinar GBM com split por grupo `(imagem, caixa)`; medir AUC-PR | 2–3 dias |
| 2.5 | Calcular SHAP (ranking, direções, interações de 2ª ordem, bootstrap) | 2–3 dias |
| 2.6 | Se sinal fraco: pilotar e validar alternativa de aprendizagem em grupos | +1 semana, contingente |
| 2.7 | **Portão de fase**: AUC-PR acima do piso e ranking estável com ≥2 features de sinal | — |

### Fase 2.5 — Validação leve de generalização (estimado: 1–1,5 semana, GPU ~zero)

| Tarefa | Descrição | Estimativa |
|---|---|---|
| 2.5.1 | Repetir Estágio A no segundo dataset-alvo | 4–5 dias |
| 2.5.2 | Comparar ranking de features entre os dois domínios | 2 dias |

### Fase 3 — Estágio B, fatorial de confirmação (estimado: 3–5 semanas, GPU pesada)

| Tarefa | Descrição | Estimativa |
|---|---|---|
| 3.1 | Definir fatores finais (ou clusters) e resolução do design fatorial | 2–3 dias |
| 3.2 | Montar células com N de crops fixo e proporção de fonte balanceada | 2–3 dias |
| 3.3 | Rodar todas as células × n seeds + controle real-sobreamostrado sem sintéticos | 2–4 semanas GPU (depende da cota) |
| 3.4 | ANOVA fatorial, effect sizes padronizados, leave-one-seed-out | 3–4 dias análise |
| 3.5 | **Portão de fase**: todas as células concluídas ou particionamento documentado por cota | — |

### Fase 4 — Síntese e redação (estimado: 4–6 semanas)

| Tarefa | Descrição | Estimativa |
|---|---|---|
| 4.1 | Confrontar previsões da Fase 0 com os resultados obtidos | 2–3 dias |
| 4.2 | Preparar repositório de reprodutibilidade público (código + dados liberáveis) | 1 semana |
| 4.3 | Redigir o artigo (metodologia, resultados, discussão, limitações) | 2–3 semanas |
| 4.4 | Revisão interna de rigor (par cego dentro do grupo, checagem de cada afirmação contra dado) | 3–5 dias |
| 4.5 | Selecionar periódico-alvo final e adaptar formatação/escopo | 2–3 dias |
| 4.6 | Submissão | — |

### Resumo de duração total estimada

**Execução ativa (Fase -1 até submissão): aproximadamente 4 a 5 meses**, sem
contar filas de revisão do periódico (tipicamente 6 a 18 meses adicionais em
Q1, com possíveis rodadas de major revision que podem exigir experimentos
suplementares). Esta estimativa assume disponibilidade contínua de cota de GPU
na Fase 3 (o item mais sensível a atraso) e resolução tempestiva da decisão de
disponibilidade de dados (item -1.7, que pode ter prazo administrativo fora do
controle da equipe técnica).

---

*Próximo passo, se aprovado: iniciar Fase -1, tarefa -1.1 (criação do
repositório).*

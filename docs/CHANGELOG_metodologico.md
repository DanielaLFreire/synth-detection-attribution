# Changelog metodológico

Registro cronológico das decisões metodológicas tomadas durante a execução
deste projeto — insumo direto para a seção de métodos e para respostas a
revisores. Cada entrada deve dizer: **o que** foi decidido, **por que**, e
**com que evidência ou referência**. Atualizar a cada decisão relevante, não
em lote no final.

Este arquivo é distinto do `CHANGELOG.md` da raiz (que registra mudanças de
*software*, não decisões de *pesquisa*).

---

## 2026-08-31 — Fundação do projeto

- **Decisão**: projeto tratado como independente do repositório anterior
  `maritime-crossdomain`, com repositório, baseline e pré-registro próprios.
  Lições metodológicas do projeto anterior são reaproveitadas e citadas
  explicitamente onde usadas, não herdadas tacitamente.
- **Decisão**: segundo dataset-alvo de validação de generalização = UA-DETRAC
  (Wen et al., 2020). Justificativa completa em
  `docs/PLANO_v2_atribuicao_causal_composicao_sintetica.md`, §2.3.
- **Decisão**: dados e artefatos pesados (imagens, crops, sintéticas,
  checkpoints) armazenados em subpasta nova dentro do Google Drive existente
  (`PROJETO_MARINHA/EXPERIMENTO_ATRIBUICAO_CAUSAL/`), não em árvore isolada.
  Datasets-fonte brutos são reaproveitados por referência (read-only); crops
  já segmentados e sintéticos do projeto anterior **não** são reaproveitados,
  pois foram extraídos sob filtros inconsistentes entre fontes — ver §12.1 do
  plano para a justificativa completa e a lista exata do que é herdado vs.
  regenerado.
- **Decisão**: licença MIT para o código deste repositório (placeholder de
  autoria em `LICENSE` e `CITATION.cff` a preencher pela equipe).
- **Decisão**: repositório criado com visibilidade **pública** desde o
  primeiro commit (`https://github.com/DanielaLFreire/synth-detection-attribution`).
  Implicação metodológica registrada: o histórico de commits do Git passa a
  ser verificável por terceiros a partir de agora — em particular, o commit
  de pré-registro da Fase 0 (previsões falsificáveis, §9 do plano) terá
  data/hora conferíveis publicamente como evidência de que foi escrito antes
  dos resultados do Estágio A/B, reforçando o valor do pré-registro como tal.

## 2026-08-31 — Auditoria de artefatos herdados no Drive (tarefa -1.9)

- **Achado**: a verificação automatizada da estrutura do Drive (script de
  checagem rodado no Colab) não encontrou nenhum artefato proibido dentro de
  `EXPERIMENTO_ATRIBUICAO_CAUSAL/` — a barreira contra reaproveitamento de
  crops/sintéticos com filtro inconsistente está intacta. Ver §12.1 do plano.
- **Esclarecimento registrado**: dois arquivos em `Datasets/_zips` não
  estavam documentados em nenhuma fonte já lida (`dataset_25k_v2.zip`,
  `SeaShips_voc_incompleto_6509.zip`). Identificação de `dataset_25k_v2.zip`:
  corresponde aos subconjuntos curado-por-similaridade-CLIP e
  aleatório-de-controle (~25 mil imagens cada) do InaTechShips, usados no
  artigo original (Freire, Teixeira & Moreira, 2026 — em revisão) nos braços
  "A (curated)" e "B (random pool)" — pré-treino direto com imagens inteiras,
  resultado de transferência negativa já estabelecido. **Decisão: fora do
  escopo deste projeto** — categoricamente distinto da composição in-place
  investigada aqui (imagens inteiras, não crops; pergunta de pesquisa
  diferente, já respondida). Não é herdado nem regenerado; permanece apenas
  como referência histórica em `Datasets/_zips`.
- **Pendente**: identificação de `SeaShips_voc_incompleto_6509.zip` ainda não
  confirmada — não usar até que a equipe esclareça se é uma versão parcial
  do SeaShips (o nome sugere isso) que poderia ser confundida com o
  `SeaShips_voc.zip` completo na extração de crops.

## 2026-08-31 — Resolução: origem do `SeaShips_voc_incompleto_6509.zip`

- **Achado, via histórico de conversas do projeto anterior**: durante o
  diagnóstico de uma discrepância no held-out zero-shot do SeaShips (a âncora
  histórica de julho/2026 era 6.979 imagens), uma checagem de duplicatas
  revelou que o `SeaShips_voc.zip` então em uso continha apenas 6.509
  arquivos únicos. A hipótese de que o `seaship.zip` (Kaggle, 7.000 imagens)
  fosse a fonte correta foi testada e descartada (0 anotações VOC nesse
  zip — não poderia ter gerado o held-out anotado). A fonte correta era a
  pasta `SeaShips_voc_completo/` no Drive, com 6.979 XMLs e 6.979 imagens
  batendo com a âncora. Conclusão: `SeaShips_voc.zip` era um zipamento
  parcial/interrompido (provável download incompleto via Roboflow).
- **Correção já aplicada pelo projeto anterior**: o zip incompleto foi
  renomeado para `SeaShips_voc_incompleto_6509.zip` (preservado por
  auditabilidade, não apagado) e um `SeaShips_voc.zip` canônico (6.979
  imagens, 0,63 GB) foi regenerado a partir da pasta completa do Drive.
- **Decisão para este projeto**: `SeaShips_voc_incompleto_6509.zip` é
  artefato obsoleto, mantido apenas como registro histórico de auditoria —
  **nunca usar como fonte de extração de crops**. Antes de configurar a
  extração do SeaShips (tarefa -1.6), confirmar que `SeaShips_voc.zip` (sem
  o sufixo) ainda corresponde à versão canônica de 6.979 imagens — contagem
  simples de arquivos, não assumir.
- **Nota de método a reaproveitar na seção de métodos do artigo**: este é um
  exemplo concreto do tipo de auditoria de proveniência que a Fase 0 deste
  projeto (§9 do plano) formaliza como pré-requisito — a discrepância só foi
  detectada porque uma contagem-âncora de referência (6.979) existia e foi
  checada antes de prosseguir. É o mesmo princípio por trás do requisito de
  manifesto com hash por artefato (§12.1): sem um número de referência
  auditável, esse tipo de corrupção silenciosa de dado passa despercebido.

## 2026-08-31 — `SeaShips_voc.zip` contém duplicatas por augmentation (Roboflow)

- **Achado**: verificação direta do zip mostrou 13.105 imagens totais, mas
  apenas **6.979 bases únicas** (batendo com o canônico já estabelecido) —
  **6.126 bases têm mais de uma cópia**, confirmando que a exportação via
  Roboflow aplicou aumento de dados (flip/rotação/brilho) sobre a maior parte
  do conjunto de treino, preservando o nome-base e variando o hash de sufixo.
- **Por que isso importa**: usar as cópias aumentadas como fonte de crops
  inflaria artificialmente a diversidade aparente do pool (a feature
  `novidade_pool`, §6 do plano, mediria pares quase-duplicados como se fossem
  amostras independentes) — um viés diferente do zip incompleto anterior,
  mas igualmente prejudicial à validade do Estágio A.
- **Decisão**: a extração de crops do SeaShips (tarefa -1.3/-1.6) deve
  deduplicar por base antes de segmentar — manter exatamente uma cópia por
  base (critério: primeira por ordem alfabética do sufixo de hash, para ser
  determinística e documentável no manifesto de extração). Implementar esse
  filtro como parte do componente de filtro unificado (§8.1 do plano), não
  como um passo ad-hoc separado.

## 2026-08-31 — Inspeção da estrutura do CITRA-3D-Real (tarefa -1.2, preparação)

- **Achado positivo**: `labels_single_class/` está confirmado **limpo (só
  classe `0`)** nos três splits (train 1.348, val 332, test 401), diretamente
  no disco — não depende de conversão em runtime como o projeto anterior
  chegou a documentar em uma versão anterior deste dataset.
- **Explicação da limpeza**: uma pasta `_quarantine/` (log
  `quarantine_log.json`, datado de 2026-04-10) documenta a remoção cirúrgica
  de duas imagens com anotação corrompida (`Quadrado_marcacao(Clone)`,
  incluindo uma bounding box degenerada com largura/altura zero) — uma do
  train (`29.04.2022-14-59-27`), uma do test (`14.04.2022-13-48-55`). Ambas
  as imagens (não só a linha inválida) foram movidas para quarentena, com
  registro completo de origem/destino de cada arquivo. Os totais atuais
  (1.348/332/401) já refletem essa remoção. Boa prática a citar no artigo
  como exemplo de auditoria de proveniência de dado.
- **Taxonomia original documentada** (`data.yaml.original`, 9 classes):
  Militar, Barca, Mercante, Vela, Passageiro, TUG, Lancha, Miúda, Navio —
  colapsadas para a classe única `embarcacao` em `data_single_class.yaml`.
  Útil para a seção de descrição de dataset do artigo.
- **Divergência encontrada entre perfis estruturais legados — NÃO
  reconciliada**: `escala_citra3d_report.json` (gerado 2026-04-23, script de
  origem não localizado) reporta 71,6% de objetos "small" (COCO@640); a
  tabela oficial do Passo Zero do projeto anterior (26/06/2026, via
  `src/crossdomain/profiling.py`) reporta 82,2% para o mesmo dataset. A área
  mediana bate entre os dois (~0,099%), mas o %small diverge — consistente
  com os dois scripts aplicarem correção de letterbox (proporção original da
  imagem) de formas diferentes ao converter bbox normalizada para pixels
  absolutos em 640×640.
- **Decisão**: nenhum dos perfis estruturais legados (`escala_citra3d_report.json`,
  tabela do Passo Zero do `maritime-crossdomain`, `07_profile_heldout_sizes.py`)
  é reaproveitado diretamente. A tarefa **0.1** deste projeto escreve um
  script de perfilamento canônico único, com o método de conversão para
  pixels absolutos documentado explicitamente (citando a definição original
  de "small object" de Lin, T.-Y. et al., 2014, "Microsoft COCO: Common
  Objects in Context", ECCV), e registra esta divergência como nota
  metodológica no artigo — é evidência de auditoria de rigor, não uma falha
  a esconder.

## 2026-08-31 — Causa raiz da divergência de perfil estrutural, identificada e confirmada

- **Origem do `escala_citra3d_report.json` localizada**: script
  `analisar_escala_citra3d.py` (394 linhas), de uma fase anterior ao
  `maritime-crossdomain` — o script que originou a própria ideia de
  composição in-place ("Scale-Aware Copy-Paste com SAM"). Saída de console
  registrada no histórico bate exatamente com o JSON (71,6% small).
- **Causa raiz identificada**: `analisar_escala_citra3d.py` converte largura
  e altura normalizadas do YOLO para pixels multiplicando cada uma por 640
  **independentemente** — equivalente a assumir implicitamente que a imagem
  original é quadrada (um *stretch* para 640×640). O Passo Zero oficial do
  `maritime-crossdomain` (`src/crossdomain/profiling.py`), usado na Tabela I
  do artigo, calcula um único fator de escala `s = 640 / max(W, H)` a partir
  das dimensões reais da imagem e aplica esse fator aos dois eixos — o
  redimensionamento com preservação de proporção ("letterbox") que o YOLO
  de fato usa no pré-processamento de treino.
- **Confirmação empírica**: as imagens do CITRA-3D-Real **não são
  quadradas** — amostra de 50 imagens do split de treino mostrou
  1920×1061 (42 imagens) e 1920×1080 (8 imagens), aspecto ~1,81:1
  (verificado via PIL em 2026-09-01). Isso confirma que o método de
  `analisar_escala_citra3d.py` distorce a conversão de forma diferente em
  cada eixo, alterando artificialmente quantos objetos caem abaixo do
  limiar de 32×32 px — exatamente a divergência observada (71,6% vs 82,2%),
  sem afetar a área normalizada (adimensional, não depende dessa conversão,
  por isso bateu igual nos dois: ~0,099%).
- **Decisão fechada**: o número correto é **82,2% small (método letterbox)**,
  porque reflete o pré-processamento real de treino — e é o único dos dois
  métodos que preserva comparabilidade justa entre datasets de proporções
  nativas diferentes (o stretch introduz uma distorção cujo tamanho varia
  dataset a dataset, conforme a proporção nativa de cada um, o que
  prejudica em vez de ajudar a comparação). O script canônico de
  perfilamento da tarefa 0.1 implementa exclusivamente o método letterbox,
  citando Lin et al. (2014) para a definição do limiar de tamanho.

## 2026-09-01 — Uso do split de validação nas colagens de sondagem: vazamento?

- **Questão levantada**: usar o split de validação para gerar as colagens de
  sondagem do Estágio A (§5.2) conta como "usar" um split reservado, e por
  isso poderia comprometer alguma medição futura?
- **Resposta**: não compromete a separação causal observação→confirmação,
  porque a métrica de decisão do Estágio B é lida no split de **teste**
  (nunca tocado pelo Estágio A). A forma de contaminação que precisaria de
  atenção seria indireta — se o checkpoint usado para rotular acerto/erro no
  Estágio A fosse escolhido por desempenho no val (early stopping clássico),
  ele estaria levemente favorecido para ir bem nesses fundos especificamente.
- **Resolvido por construção**: o protocolo V2 (§3 do plano) já especifica
  seleção de checkpoint por **época pré-registrada fixa**, nunca por métrica
  de validação — decisão tomada por outro motivo (instabilidade de seleção
  por val em conjuntos pequenos), mas que elimina também esta lacuna como
  efeito colateral. Nenhuma mudança de protocolo foi necessária; só a
  conexão explícita entre as duas decisões foi registrada no plano (§5.2).
- **Referência conceitual usada no raciocínio**: Hastie, T., Tibshirani, R.,
  Friedman, J. (2009). *The Elements of Statistical Learning* (2ª ed.),
  Cap. 7 "Model Assessment and Selection" — fundamenta a distinção entre o
  papel do split de validação (seleção de modelo) e do split de teste
  (estimativa de erro de generalização), e por que só o segundo precisa
  ficar intocado até a Fase 4.

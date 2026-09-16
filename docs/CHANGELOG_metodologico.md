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

## 2026-09-01 — Tarefa -1.3, entrega parcial: filtro de crop unificado

- **Escopo entregue**: (1) deduplicação de imagens aumentadas por exportação
  Roboflow (`src/extraction/dedup_roboflow.py`) — implementa a correção
  decidida em 2026-08-31 para o `SeaShips_voc.zip`; (2) filtro de qualidade
  de crop unificado (`src/extraction/quality_filter.py`), com limiares de
  dimensão mínima e cobertura de máscara **configuráveis, não fixos**; (3)
  manifesto de extração com hash SHA-256 por crop mantido
  (`src/extraction/quality_manifest.py`), produzindo diretamente o formato
  `pool_crops` consumido por `src.compose.compor_dataset` (integração entre
  as tarefas -1.2 e -1.3 confirmada por teste).
- **Decisão deliberada de não fixar o limiar de dimensão mínima agora**: o
  projeto anterior usou 20px, calibrado especificamente para o ABOShips
  (66,3% de suas caixas têm lado menor que 50px). Copiar esse número para
  as quatro fontes deste projeto sem re-verificação repetiria o tipo de
  decisão que causou o confound documentado entre ABOShips e InaTechShips.
  `FiltroConfig.min_dim_px` é parâmetro obrigatório sem valor padrão — o
  valor correto será derivado na tarefa **0.2** (perfis das fontes), a
  partir da distribuição de tamanho real das quatro fontes deste projeto.
- **Escopo NÃO entregue nesta tarefa** (deferido para a -1.6): leitura da
  anotação nativa de cada fonte (CSV do ABOShips, formato do SMD) para
  realizar a extração propriamente dita dos crops a partir das imagens
  brutas — só verificamos com certeza o formato do CITRA (YOLO) e do
  SeaShips (VOC XML) até agora. Este módulo opera sobre crops **já
  extraídos** (arquivos de imagem individuais); não lê anotação de origem.

## 2026-09-01 — Tarefa -1.4: materialização de `labels_final/` com hash

- **Entregue**: `src/materialize/labels_final.py` — valida integridade
  (correspondência 1:1 imagem↔label, todas as linhas com classe permitida)
  antes de copiar `labels_single_class/` para `labels_final/` em cada split,
  gravando um manifesto (`labels_final_manifest.json`) com hash SHA-256 por
  arquivo e contagem de boxes. Função separada de verificação
  (`verificar_labels_final`) recalcula hashes a qualquer momento futuro e
  reporta deriva (arquivo alterado, faltando, ou novo não registrado).
- **Teste deliberado**: um dos testes reproduz em miniatura a exata
  contaminação real já encontrada no CITRA-3D-Real
  (`Quadrado_marcacao(Clone)`) e confirma que a materialização a detecta e
  aborta sozinha — não dependemos mais de uma quarentena manual feita à
  parte para garantir isso; o script recusaria materializar um dado
  contaminado como esse, caso reaparecesse.
- **Ação pendente para você rodar no Colab** (não fiz isso — não tenho
  acesso ao Drive real): executar
  `scripts/materializar_labels_final.py` apontando para
  `CITRA-3D-Real`, com `labels_subfolder_origem=labels_single_class` e
  `splits=[train, val, test]`. Como já confirmamos que os três splits estão
  limpos, a expectativa é que a materialização complete sem levantar
  `InconsistenciaDeDataset` — se levantar, é sinal de que algo mudou no
  Drive desde a nossa verificação de 2026-08-31/09-01, e deve ser
  investigado antes de prosseguir para a Fase 0.

## 2026-09-01 — Tarefa -1.4 executada com sucesso no Drive real

- **Resultado**: `labels_final/` materializado nos três splits do
  CITRA-3D-Real, com manifesto de hash gerado em cada um. Nenhuma
  `InconsistenciaDeDataset` foi levantada.
- **Contagens** (train / val / test): 1.348 / 332 / 401 imagens;
  4.489 / 1.267 / 1.247 boxes; **7.003 boxes no total** — bate exatamente
  com `n_bboxes_total` do `escala_citra3d_report.json` investigado
  anteriormente, confirmando de forma independente (validação por código
  distinto do que gerou aquele relatório) que os três splits têm
  exclusivamente classe `0`, sem imagem ou label órfão.
- **Estado**: `labels_final/` e `labels_final_manifest.json` (um por split)
  agora existem em `CITRA-3D-Real/{split}/` no Drive. Este é o artefato
  **oficial e congelado** a partir de agora — qualquer script deste projeto
  que precisar de labels do dataset-alvo deve ler de `labels_final/`, não
  de `labels_single_class/` diretamente (ainda que hoje sejam idênticos, só
  `labels_final/` tem o manifesto de hash que permite detectar deriva).
  Rodar `scripts/verificar_labels_final.py` antes de cada fase que dependa
  destes dados (Fase 0 em diante) é recomendado, não apenas nesta ocasião.

## 2026-09-01 — Tarefa -1.5: protocolo de treino V2 em código

- **Bug corrigido**: `src/train/protocol.py` implementa warmup em passos de
  gradiente **absolutos**, não em épocas. Documentado no projeto anterior:
  a campanha original definiu warmup em épocas, o que produziu 252 steps de
  warmup real no baseline B2 contra um número muito maior nos braços joint
  (que têm o dobro de imagens por época, real+sintético) — mesma contagem
  nominal de "épocas de warmup", quantidade real de aquecimento bem
  diferente entre braços. `calcular_warmup_epochs_equivalente()` calcula,
  para cada braço, a fração de época que resulta no mesmo número real de
  passos, dado `warmup_steps_alvo` constante.
- **Regra imposta em código, não só documentada**: `early_stopping_habilitado`
  deve ser sempre `False` — o construtor de `ProtocoloTreinoV2` levanta
  `ProtocoloInvalido` se receber `True`. Early stopping por métrica de
  validação equivale a selecionar o checkpoint pelo desempenho no val, o
  mesmo problema já discutido e resolvido para o Estágio A (ver entrada de
  2026-09-01 sobre vazamento via split de validação) — agora fechado também
  no protocolo de treino em si.
- **`epoca_checkpoint` é obrigatório, sem valor padrão**: o construtor
  recusa instanciar o protocolo sem esse valor — força a decisão consciente
  de qual época usar como checkpoint fixo, a ser preenchida com evidência
  de convergência da piloto (Fase 1), nunca copiada de outro projeto.
- **Teste de contraste incluído deliberadamente**
  (`test_bug_reproduzido_sem_a_correcao_para_contraste`): mostra o que
  aconteceria SEM a correção — confirma que o bug documentado é real e
  reproduzível, não uma leitura exagerada do changelog anterior.
- **Escopo NÃO coberto nesta tarefa**: os valores numéricos reais de
  `epochs_total`, `epoca_checkpoint` e `warmup_steps_alvo` para os braços
  deste projeto — esses vêm da piloto da Fase 1, ainda não executada. O
  código está pronto para receber esses valores assim que existirem.

## 2026-09-01 — Tarefa -1.6 (primeira fonte, SMD): estrutura verificada e extrator escrito

- **Estrutura real do SMD verificada** (`smd_clean.zip`, 1.839 entradas):
  914 imagens `.jpg` + 914 labels `.txt`, formato YOLO, classe única
  (`nc: 1`, `names: ['vessel']`). Sem duplicação por augmentation Roboflow
  (914 bases únicas = 914 imagens — diferente do SeaShips).
- **Achado estrutural**: as 914 imagens estão **todas** dentro de
  `smd_clean/test/` — `train/` e `val/` estão vazios. Números batem
  exatamente com "SMD on-shore: 914 imagens, 7.043 boxes" já documentado no
  perfil estrutural do projeto anterior — resquício, provavelmente, de uma
  fase em que o SMD foi cogitado como candidato a held-out (papel
  posteriormente atribuído ao SeaShips). **Decisão**: para este projeto, o
  SMD é tratado como um pool único de 914 imagens (a divisão train/val/test
  daquele zip é ignorada — não é papel do SMD neste desenho).
- **Achado adicional, registrado para uso futuro**: as imagens do SMD são
  frames de 36 vídeos distintos (~11–35 frames cada, identificáveis pelo
  padrão de nome `MVI_<id>[_VIS|_NIR][_Haze]_frame<N>`). Frames do mesmo
  vídeo são mais correlacionados entre si do que frames de vídeos
  diferentes — uma forma de quase-duplicação por conteúdo, distinta da
  duplicação por nome de arquivo do Roboflow, mas com efeito análogo sobre
  a diversidade aparente do pool. O extrator (`extrair_crops_de_yolo`)
  já captura `video_id` no manifesto de extração para permitir análise ou
  amostragem por vídeo mais tarde, mesmo que a decisão de como tratar isso
  (ex.: limitar N crops por vídeo) ainda não tenha sido tomada — decisão
  deferida para quando o perfil das fontes (tarefa 0.2) mostrar se isso
  afeta materialmente a diversidade medida do pool.
- **Entregue**: `src/extraction/extrair_crops_yolo.py` — extrai um arquivo
  de crop por bounding box a partir de anotação YOLO (recorte retangular
  simples, não segmentação SAM — ver nota de escopo abaixo). Caixas
  degeneradas ou labels órfãos são pulados e registrados no manifesto, sem
  interromper o lote inteiro (decisão deliberadamente menos estrita que a
  materialização de `labels_final/`, porque aqui lidamos com uma fonte de
  crops, não com o dataset-alvo — uma caixa ruim isolada não compromete o
  experimento). `scripts/extrair_smd.py` conecta extração + filtro
  unificado (-1.3) + cópia para o Drive numa única execução. Coberto por
  `tests/test_extrair_crops_yolo.py` (6 testes, incluindo reconhecimento de
  `video_id` com os nomes de arquivo reais do SMD) — todos passando. Suíte
  completa: 37/37.
- **Escopo NÃO coberto nesta entrega**: modo de segmentação SAM (só recorte
  retangular por enquanto — decisão de qualidade de borda a revisitar se
  necessário); extração do SeaShips (precisa primeiro rodar a deduplicação
  Roboflow já implementada em -1.3, ainda não conectada a um script de
  ponta a ponta como o do SMD); extração do ABOShips (formato CSV ainda não
  inspecionado nesta sessão).
- **Aviso registrado**: `scripts/extrair_smd.py` usa `min_dim_px` como
  parâmetro **obrigatório**, sem valor padrão sensato definido — o exemplo
  na documentação do script (32px) é ilustrativo, não uma recomendação. O
  valor real só deve ser decidido na tarefa 0.2, a partir da distribuição
  de tamanho medida nas quatro fontes deste projeto.

## 2026-09-01 — Tarefa -1.6 (segunda fonte, SeaShips): extrator VOC e script de ponta a ponta

- **Entregue**: `src/extraction/extrair_crops_voc.py` — extrai um crop por
  `<object>` de cada anotação VOC XML. Diferente do extrator YOLO (SMD): a
  caixa já vem em pixels absolutos, sem conversão por dimensão de imagem.
  Cada objeto pode ter uma subclasse original do SeaShips (dataset original
  tem 6 tipos de embarcação) — capturada no manifesto como
  `classe_original_fonte`, mas **não usada para filtrar**, já que este
  projeto usa o SeaShips apenas como fonte de aparência visual para a
  classe única do dataset-alvo.
- **Checagem de auditoria incluída de graça**: comparação entre as
  dimensões declaradas no `<size>` do XML e o tamanho real do arquivo de
  imagem, registrada por linha (`dimensoes_xml_conferem_com_imagem`) —
  sinaliza, sem abortar, uma possível fonte de inconsistência (imagem
  redimensionada depois da anotação).
- **`scripts/extrair_seaships.py`** conecta as três etapas: (1) extrai o
  zip localmente, (2) aplica a deduplicação Roboflow já implementada em
  -1.3 sobre as imagens brutas (13.105 → ~6.979 esperado, achado de
  2026-08-31), movendo cada imagem única + seu XML correspondente para uma
  pasta separada antes de prosseguir, (3) extrai crops via VOC apenas
  sobre o conjunto já deduplicado, (4) aplica o filtro unificado, (5) copia
  para o Drive. A ordem importa: deduplicar ANTES de extrair evita gastar
  processamento em crops que seriam quase-idênticos entre si por
  augmentation.
- Coberto por `tests/test_extrair_crops_voc.py` (4 testes: extração básica,
  preservação de classe original, divergência de dimensões XML×imagem,
  caixa degenerada) — todos passando. Suíte completa: 41/41.
- **Escopo NÃO coberto ainda**: execução real contra o `SeaShips_voc.zip`
  do Drive (script pronto, mas não rodado nesta sessão); extração do
  ABOShips (formato CSV, ainda não inspecionado).

## 2026-09-01 — Tarefa -1.6 (terceira fonte, ABOShips): estrutura verificada e extrator escrito

- **Estrutura real do ABOShips verificada** (`ABOships.zip`, 9.899
  entradas): 9.880 imagens `.png`, um único arquivo de anotação
  `ABOshipsDataset/Labels/Vesibussi_Labels.csv` com colunas
  `filename,width,height,class,xmin,xmax,ymin,ymax`. Imagens distribuídas
  em 16 subpastas por data (`Seaships/20180626/` a `Seaships/20180708/`).
- **Achado confirmado por verificação numérica direta** (não herdado sem
  checagem): `width`/`height` do CSV são as dimensões da **caixa**
  (`xmax-xmin`, `ymax-ymin`), não da imagem — conferido na primeira linha
  de amostra (width=38 = 520-482; height=24 = 339-315). Consistente com a
  suspeita registrada no changelog do projeto anterior, agora comprovada
  com números, não apenas citada.
- **Achado parcialmente confirmado, tratado com cautela**: as 5 imagens de
  amostra verificadas são todas 1280×720, consistente com a suposição
  herdada de "imagem sempre 1280×720" — mas **essa suposição não foi
  codificada** no extrator. `extrair_crops_de_csv_abo` sempre abre a
  imagem real para obter as dimensões (mesmo princípio já aplicado a SMD e
  SeaShips), evitando risco caso alguma imagem, entre as 9.880, fuja dessa
  dimensão (não verificamos as 9.880, só uma amostra de 5).
- **Entregue**: `src/extraction/extrair_crops_csv_abo.py` — indexa todas as
  imagens por nome-base entre as 16 subpastas de data antes de processar o
  CSV (o CSV não referencia a subpasta), com detecção de nome-base ambíguo
  (`NomeBaseAmbiguo`) caso duas imagens em subpastas diferentes
  compartilhem o mesmo nome-base. Agrupa linhas do CSV por `filename`
  (múltiplas caixas por imagem são suportadas) e registra, por caixa, uma
  checagem de consistência entre `width`/`height` do CSV e a bbox derivada
  de xmin/xmax/ymin/ymax. `scripts/extrair_aboships.py` conecta extração +
  filtro unificado (-1.3) + cópia para o Drive. Coberto por
  `tests/test_extrair_crops_csv_abo.py` (6 testes) — todos passando. Suíte
  completa: 47/47.
- **Fase -1.6 agora coberta para as três fontes públicas de crops (SMD,
  SeaShips, ABOShips)** — falta apenas rodar os três scripts contra os
  dados reais no Drive (nenhum foi executado além do teste sintético nesta
  sessão) e decidir `min_dim_px` na tarefa 0.2.

## 2026-09-01 — Tarefa -1.8: UA-DETRAC verificado e preparado como segundo domínio

- **Decisão sobre proveniência**: diante de múltiplos espelhos comunitários
  incompatíveis do UA-DETRAC no Roboflow Universe (sem uma versão oficial
  de acesso imediato), aplicamos o MESMO padrão de rigor já usado para
  SMD/SeaShips/ABOShips — não uma exigência nova: escolhida uma versão
  específica e documentada (`UA-DETRAC-DATASET-10K` por `rjacaac1`,
  Roboflow Universe, versão 2, ~9.816 imagens, 4 classes), com URL e autor
  registrados para citação, em vez de qualquer espelho não identificado.
- **Estrutura real verificada**: 9.816 imagens/labels em `train/` (9.316) e
  `valid/` (500); `test/` vazio (sem problema — o papel do UA-DETRAC neste
  projeto, Fase 2.5, usa apenas inferência com detector já treinado
  (COCO), não requer split de teste próprio). Formato YOLO (reaproveita o
  extrator já escrito para o SMD, nenhum extrator novo necessário). 4
  classes originais (`bus`, `car`, `truck`, `van`, `data.yaml` verificado)
  — precisam de colapso para classe única `vehicle`, mesmo tratamento já
  dado às 9 classes do CITRA-3D-Real.
- **Duplicação por augmentation Roboflow confirmada, escala pequena**: 100
  de 9.816 imagens do train têm mais de uma cópia — mesmo mecanismo do
  SeaShips (13.105→6.979), proporção bem menor aqui. Deduplicado pelo
  mesmo módulo (`dedup_roboflow.py`) por consistência de método, não por
  o impacto ser grande neste caso.
- **Entregue**: `src/materialize/collapse_classes.py` — transforma label
  multi-classe em classe única (diferente de `materializar_labels_final`,
  que só valida, não converte), com detecção de classe fora do conjunto
  declarado (`ClasseOriginalInesperada`). `scripts/preparar_ua_detrac.py`
  encadeia: extração do zip → colapso de classes (train e valid) →
  deduplicação Roboflow (train) → materialização de `labels_final/` do
  split **valid** (fundo de composição da Fase 2.5, seguindo a mesma regra
  §5.2 de nunca usar o split usado para ajuste do detector) → extração do
  pool de crops de veículo a partir do split **train** deduplicado →
  filtro unificado → cópia para o Drive. Nenhum extrator novo foi
  necessário — reaproveita `extrair_crops_de_yolo` (SMD) e
  `filtrar_pool_de_crops`/`materializar_labels_final` já existentes.
  Coberto por `tests/test_collapse_classes.py` (3 testes) — todos
  passando. Suíte completa: 50/50.
- **Fase -1 concluída** com esta entrega: todas as nove tarefas (-1.1 a
  -1.9) têm código escrito e testado. Pendências reais remanescentes antes
  da Fase 0: rodar os quatro scripts de extração (SMD, SeaShips, ABOShips,
  UA-DETRAC) contra os dados reais no Drive — nenhum foi executado além de
  testes sintéticos nesta sessão — e decidir `min_dim_px` (tarefa 0.2, com
  base na distribuição de tamanho real das quatro fontes).

## 2026-09-01 — Início da Fase 0: perfilamento estrutural canônico (tarefa 0.1)

- **Entregue**: `src/profiling/target_profile.py` — reimplementa do zero
  (não porta o artefato antigo, porta o MÉTODO já validado) a classificação
  COCO-style small/medium/large via letterbox: fator de escala único
  `s = eval_size / max(W, H)` a partir das dimensões reais de cada imagem,
  aplicado igualmente aos dois eixos — método correto confirmado em
  2026-09-01 contra o método stretch (que causou a divergência 71,6% vs.
  82,2% já diagnosticada e resolvida).
- **Teste central** (`test_letterbox_e_stretch_divergem_para_imagem_nao_quadrada`):
  reproduz numericamente, com uma caixa de 80×80 pixels originais numa
  imagem 1920×1080, que os dois métodos produzem categorias DIFERENTES
  para a mesma caixa (`small` por letterbox, `medium` por stretch) — prova
  de que a divergência diagnosticada antes é reproduzível sob demanda, não
  apenas uma leitura pontual de um relatório antigo. Teste de controle
  confirma que os métodos coincidem quando a imagem é quadrada — isolando
  a não-quadratura como a causa, não um bug genérico.
- `scripts/perfilar_citra.py` roda o perfilamento sobre os três splits do
  CITRA-3D-Real usando `labels_final/` (materializado e verificado em
  -1.4), gera um perfil consolidado, e salva em JSON versionável.
- Coberto por `tests/test_target_profile.py` (5 testes) — todos passando.
  Suíte completa: 55/55.
- **Ação pendente para você rodar no Colab**: executar
  `scripts/perfilar_citra.py` para gerar o perfil real do CITRA-3D-Real —
  ainda não fiz isso, não tenho acesso ao Drive.

## 2026-09-01 — Tarefa 0.1 executada: perfil canônico do CITRA-3D-Real gerado

- **Resultado real** (via `scripts/perfilar_citra.py`, `labels_final/`):
  train 4.489 boxes (81,8% small), val 1.267 boxes (85,7% small), test
  1.247 boxes (79,9% small). Consolidado: **7.003 boxes, 2.081 imagens**,
  small ponderado = (3.674+1.086+996)/7.003 = **82,2%**.
- **Convergência independente confirmada**: os 7.003 boxes / 2.081 imagens
  batem com a materialização de `labels_final/` (tarefa -1.4, três fontes
  de código diferentes agora concordam: materialização, perfil legado do
  Passo Zero, perfil novo). O percentual consolidado de 82,2% small bate,
  até a primeira casa decimal, com o valor do Passo Zero oficial do
  projeto anterior (calculado por um código diferente do implementado
  aqui) — evidência de que a reimplementação do método letterbox está
  correta, não apenas plausível. Resultado salvo em
  `pre_registro/perfil_citra_3d_real.json` no Drive.
- **Perfil do alvo (Família 4 de features, §6 do plano) agora
  disponível e reproduzível**: percentis completos de largura/altura/área
  normalizada, aspect ratio, posição, e objetos por imagem, por split e
  consolidado — pronto para servir de referência às features relacionais
  do Estágio A quando chegarmos lá.

## 2026-09-01 — Módulo de segmentação SAM (mitigação de shortcut learning)

- **Motivação**: recorte retangular direto (usado até agora nas quatro
  fontes) carrega fundo original ao redor do objeto, criando uma borda
  visível de descontinuidade contra a cena de destino na composição. Risco
  identificado: o detector pode aprender a reconhecer a borda em si como
  pista de "objeto colado", em vez da aparência real do objeto —
  fenômeno descrito por Geirhos, R. et al. (2020), "Shortcut Learning in
  Deep Neural Networks", *Nature Machine Intelligence*, 2(11):665-673.
  Como o tom de fundo residual varia sistematicamente por fonte (água do
  SMD, céu do ABOShips, doca do SeaShips), esse risco poderia reintroduzir
  um confound "fonte" por uma via diferente da já resolvida (filtro
  inconsistente ABO vs. InaTech).
- **Decisão de design**: a segmentação roda SEMPRE sobre a imagem
  original, nunca sobre um crop já recortado — o SAM precisa de contexto
  de fundo ao redor da caixa para traçar a fronteira com precisão, e rodar
  sobre um crop minúsculo já recortado forçaria upsampling que borra a
  imagem antes da segmentação.
- **Entregue**: `src/segmentation/sam_segment.py` — interface `Segmentador`
  (qualquer objeto com `.segmentar(imagem, caixa) -> máscara`) permite
  testar toda a lógica de aplicação de máscara/recorte/cálculo de
  cobertura com um segmentador falso, sem GPU nem pesos do SAM.
  `SegmentadorSAM` real (Kirillov et al., 2023, "Segment Anything", ICCV)
  usa prompt de caixa, com import tardio de `segment_anything`/`torch`
  (não testável neste ambiente sem GPU, mas isolado o suficiente para não
  afetar a testabilidade do resto). `aplicar_mascara_e_recortar` produz um
  crop RGBA com fundo transparente fora da máscara, calculando
  `cobertura_mascara` (fração da caixa coberta) — alimenta diretamente
  `FiltroConfig.min_cobertura_mascara`, já existente desde -1.3 mas nunca
  antes populado com dado real.
- **Extrator YOLO atualizado** (`extrair_crops_de_yolo`, usado por SMD e
  UA-DETRAC): parâmetro opcional `segmentador` (default `None`, preserva
  comportamento retangular antigo sem quebrar nada já testado). Quando
  fornecido, saída é sempre `.png` (precisa de canal alpha) e o manifesto
  ganha o campo `cobertura_mascara` (manifest_version bump 1.0→1.1).
  Extratores VOC (SeaShips) e CSV (ABOShips) ainda **não** receberam a
  mesma atualização — pendência explícita, mesmo padrão a replicar.
- **Nova função de integração**: `carregar_coberturas_do_manifesto_extracao`
  lê o manifesto de extração e monta o dicionário de coberturas que
  `filtrar_pool_de_crops` (-1.3) consome — testado de ponta a ponta
  (extração com segmentador falso → filtro rejeitando por cobertura real
  abaixo do limiar exigido).
- Coberto por `tests/test_sam_segment.py` (4 testes), 3 testes novos em
  `tests/test_extrair_crops_yolo.py`, e 1 teste de integração em
  `tests/test_extraction.py`. Suíte completa: 63/63.
- **Pendências explícitas**: (1) replicar a mesma integração de
  segmentador nos extratores VOC e CSV do ABOShips/SeaShips; (2) rodar
  `SegmentadorSAM` de verdade no Colab (checkpoint SAM ViT-B, GPU) contra
  os ~143 mil crops já extraídos em modo retangular — reprocessamento
  necessário, os crops retangulares já gerados não são reaproveitáveis
  neste novo modo.

## 2026-09-01 — Segmentador replicado nos extratores VOC e CSV, e nos três scripts de ponta a ponta

- **Extrator VOC (SeaShips)** e **extrator CSV (ABOShips)** atualizados
  com o mesmo parâmetro opcional `segmentador`, mesmo contrato do extrator
  YOLO: roda sobre a imagem original, produz `.png` com canal alpha,
  registra `cobertura_mascara` no manifesto (bump de versão 1.0→1.1 em
  ambos, mesmo padrão do YOLO). Retrocompatível — testes antigos (modo
  retangular) continuam passando sem alteração.
- **As quatro fontes agora têm o mesmo mecanismo disponível e
  consistente** — não existe mais risco de uma fonte usar segmentação e
  outra não por causa de uma peça de código faltando, só por decisão
  explícita de quando rodar cada uma.
- Os três scripts de ponta a ponta (`extrair_smd.py`, `extrair_seaships.py`,
  `extrair_aboships.py`) ganharam o parâmetro `segmentador: Segmentador |
  None = None`, repassado à função de extração correspondente — sem isso,
  a capacidade existiria na biblioteca mas não seria alcançável pelos
  scripts que de fato rodamos no Colab.
- Coberto por 4 novos testes (2 no extrator VOC, 2 no CSV) seguindo
  exatamente o padrão já validado no YOLO. Suíte completa: 67/67.
- **Ainda pendente**: nenhum crop real foi reprocessado com SAM de
  verdade — as três fontes (mais UA-DETRAC) continuam com os ~143 mil
  crops já extraídos em modo retangular no Drive. Rodar o SAM de verdade
  exige GPU e o checkpoint (`sam_vit_b_01ec64.pth`).

## 2026-09-01 — SAM 3 investigado e implementado (acesso solicitado, pendente aprovação)

- **SAM 3 confirmado real e atual**: lançado pela Meta em 19/11/2025
  (`facebookresearch/sam3`, paper Carion et al., 2025, arXiv:2511.16719).
  Ponto forte declarado e relevante para este projeto: desempenho melhor
  em objetos finos, pequenos, de baixo contraste — perfil que já medimos
  como o do CITRA-3D-Real na tarefa 0.1 (mediana ~30px).
- **Licença lida na íntegra** ("SAM License", atualizada 19/11/2025):
  concede uso/reprodução/distribuição/modificação de forma ampla; exige
  reconhecimento em publicações que usem o modelo; redistribuição de
  materiais SAM (ou obras derivadas) deve carregar os mesmos termos. Ponto
  não resolvido com certeza (não somos advogados): se os CROPS gerados
  usando o modelo contam como "obra derivada dos materiais SAM" para fins
  de redistribuição — a cláusula de isenção de garantia trata "saídas e
  resultados" como parte do escopo do acordo, sem definir claramente a
  obrigação sobre eles. Não bloqueia uso interno de pesquisa; relevante se
  os crops segmentados forem publicados num repositório de reprodutibilidade
  — sinalizar para conformidade institucional nesse momento, não decidido
  unilateralmente aqui.
- **Fricção prática identificada**: acesso aos checkpoints requer
  aprovação via Hugging Face (portão de acesso), mesmo padrão de risco de
  atraso já enfrentado na decisão do UA-DETRAC (§2.3). Requisitos também
  mais pesados: Python 3.12+, PyTorch 2.7+, CUDA 12.6+.
- **Decisão**: solicitar acesso ao SAM 3 agora, escrever o código enquanto
  aguarda aprovação, testar assim que liberado. SAM 1 (Apache 2.0, sem
  portão) permanece disponível e funcional como alternativa não-bloqueada.
- **Decisão de design do `SegmentadorSAM3`**: a API pública confirmada do
  pacote `sam3` usa prompt de TEXTO (`Sam3Processor.set_text_prompt`), não
  um prompt de caixa equivalente ao `SamPredictor.predict(box=...)` do
  SAM 1/2 — não foi possível confirmar, a partir da documentação
  disponível sem acesso ao pacote instalado, o nome exato de um método de
  prompt de caixa no SAM 3 (preferimos não arriscar um nome de método não
  verificado). Solução: usar o prompt de texto (retorna máscaras+caixas
  para todas as instâncias do conceito) e selecionar, entre as instâncias
  retornadas, a de maior IoU contra a caixa de anotação já conhecida
  (`indice_melhor_iou`, função pura testada com 4 casos). Se nenhuma
  instância atingir o IoU mínimo, tratada como sem máscara disponível
  (mesmo comportamento já existente no filtro de qualidade para SAM
  ausente).
- Coberto por 4 novos testes em `tests/test_sam_segment.py`. Suíte
  completa: 71/71. O carregamento real (`SegmentadorSAM3.carregar`) não é
  testável neste ambiente (sem GPU, acesso pendente) — mesma limitação já
  aceita para `SegmentadorSAM` (SAM 1).
- **Referência adicionada**: Carion, N. et al. (2025). "SAM 3: Segment
  Anything with Concepts." arXiv:2511.16719.

## 2026-09-01 — Correção do SegmentadorSAM3: prompt de caixa confirmado por leitura direta do código-fonte

- **Achado**: clonei o repositório oficial `facebookresearch/sam3` (código
  público, só os checkpoints exigem aprovação) e li diretamente
  `sam3/model/sam3_image_processor.py`. Isso **corrigiu** a suposição
  anterior (registrada mais cedo hoje): existe sim um método de prompt de
  caixa, `Sam3Processor.add_geometric_prompt(box, label, state)`, formato
  `[cx, cy, w, h]` normalizado em [0,1] — funcionalmente equivalente ao
  `SamPredictor.predict(box=...)` do SAM 1/2. Não é preciso o esquema de
  prompt de texto + correspondência por IoU que foi implementado como
  contorno; a implementação foi reescrita para usar o método real.
- **Detalhe de uso descoberto na leitura do código, não documentado nas
  fontes secundárias consultadas antes**: `add_geometric_prompt` acumula
  caixas no estado (via `geometric_prompt.append_boxes`) em vez de
  substituir — processar múltiplas caixas da mesma imagem exige chamar
  `reset_all_prompts(state)` entre uma caixa e outra, preservando o
  encoding da imagem já calculado (`state["backbone_out"]`, não afetado
  pelo reset) mas limpando o prompt geométrico anterior. Implementado em
  `SegmentadorSAM3.segmentar()`.
- **A correspondência por IoU não foi descartada** — mantida como
  segurança adicional, já que múltiplas instâncias ainda podem passar do
  limiar de confiança mesmo com prompt de caixa; a função
  `indice_melhor_iou` já testada continua em uso, agora como salvaguarda
  em vez de mecanismo principal.
- **Nota de método**: este é um exemplo concreto de por que preferimos
  verificar contra a fonte primária quando possível, em vez de confiar só
  em buscas — a implementação anterior (baseada em documentação de
  terceiros) teria funcionado, mas de forma mais indireta e com um passo
  a mais (prompt de texto) que a API real não exige.
- Adicionados 3 testes de conversão de formato de caixa
  (`_caixa_absoluta_para_cxcywh_normalizado`), incluindo um que confirma a
  consistência com a mesma convenção cx/cy/w/h já usada em todo o projeto
  (compose.py, extrair_crops_de_yolo.py), só no sentido inverso. Suíte
  completa: 74/74.

## 2026-09-01 — SAM 3 instalado no Colab: conflito de numpy com SHAP identificado

- **Instalação do pacote `sam3` bem-sucedida** via
  `git clone` + `pip install -e .` no Colab (código público, sem portão —
  só os checkpoints exigem aprovação).
- **Conflito de dependência identificado**: `sam3` exige `numpy<2`, o que
  forçou o rebaixamento de `numpy 2.1.3` para `1.26.4` no ambiente,
  quebrando a compatibilidade declarada de vários pacotes que exigem
  `numpy>=2` já presentes no Colab -- entre eles, **`shap`**, que é a
  ferramenta central do Estágio A (§5 do plano).
- **Decisão operacional**: SAM 3 (ou SAM 1) e SHAP nunca devem ser
  instalados/usados na MESMA sessão de runtime do Colab. Segmentação de
  crops (Fase -1) e análise de importância de features com SHAP (Estágio
  A) já ocorrem em fases distintas do cronograma -- a separação de
  ambiente é uma restrição operacional a documentar, não uma mudança de
  desenho. Usar sessões de runtime dedicadas: uma para segmentação
  (sam3/segment_anything + torch), outra para análise (shap + modelo
  substituto).
- **Ação necessária**: reiniciar a sessão do Colab após a instalação do
  `sam3` (exigido pelo próprio Colab após troca de versão do numpy) antes
  de prosseguir com qualquer segmentação.

## 2026-09-02 — Acesso ao SAM 3 aprovado; bug de instalação editável corrigido

- **Acesso aos checkpoints do SAM 3 aprovado** via Hugging Face (status
  "ACCEPTED", conta institucional).
- **Bug encontrado ao carregar o modelo pela primeira vez**:
  `build_sam3_image_model()` (dentro do próprio pacote `sam3`, não código
  nosso) falha com `TypeError: expected str, bytes or os.PathLike object,
  not NoneType` ao tentar localizar `assets/bpe_simple_vocab_16e6.txt.gz`
  via `pkg_resources.resource_filename`. Causa raiz: `pkg_resources`
  (biblioteca legada de descoberta de recursos) não consegue resolver
  `sam3.__file__` quando o pacote foi instalado em modo editável
  (`pip install -e .`, PEP 660) em Python 3.13 com setuptools recente —
  `__file__` fica `None` nesse cenário, quebrando a lógica interna do
  `pkg_resources`. Bug da interação entre bibliotecas de terceiros
  (`pkg_resources` + instalação editável), não do nosso código nem da
  lógica do SAM 3 em si.
- **Correção aplicada**: `build_sam3_image_model` já aceita um parâmetro
  opcional `bpe_path` que, se fornecido, ignora completamente a busca
  automática quebrada. `SegmentadorSAM3.carregar()` foi atualizado para
  aceitar e repassar esse parâmetro — quando fornecido explicitamente
  (caminho para `assets/bpe_simple_vocab_16e6.txt.gz` dentro do clone
  local do `sam3`), o carregamento funciona normalmente. Não foi
  necessário modificar nenhum arquivo do pacote `sam3` em si.
- Suíte completa após a mudança de assinatura: 74/74 passando (a mudança
  não afeta nenhum teste existente, já que `bpe_path` é opcional e os
  testes não exercitam o carregamento real, que depende de GPU).

## 2026-09-02 — Segundo bug de terceiro corrigido: SAM 3 exige contexto autocast bfloat16

- **Erro encontrado durante a primeira inferência real**:
  `RuntimeError: mat1 and mat2 must have the same dtype, but got BFloat16
  and Float`, dentro do backbone visual do modelo (vitdet.py), não em
  código nosso.
- **Causa raiz confirmada por inspeção do código-fonte**: partes do SAM 3
  operam nativamente em bfloat16 (comentário explícito em
  `sam3/model/sam3_image.py`: features do backbone SAM2 "já estão em
  bfloat16 por causa de AMP"), mas a imagem de entrada é explicitamente
  convertida para float32 (`sam3_image.py`, linha ~154). Sem um contexto
  de precisão mista (`torch.autocast`) envolvendo a chamada, ocorre
  incompatibilidade de tipo numa camada Linear interna.
- **Confirmado como uso pretendido, não workaround improvisado**: os seis
  notebooks de exemplo oficiais (`facebookresearch/sam3/examples/`) todos
  entram em `torch.autocast("cuda", dtype=torch.bfloat16)` logo após
  carregar o modelo, antes de qualquer inferência.
- **Correção aplicada**: `SegmentadorSAM3.segmentar()` agora envolve as
  chamadas de inferência (`set_image`, `add_geometric_prompt`) num bloco
  `with torch.autocast("cuda", dtype=torch.bfloat16):` -- mais limpo do
  que o padrão dos notebooks (que entram no contexto e nunca saem,
  aceitável em notebook interativo, não numa função de biblioteca
  reutilizável).
- Suíte completa: 74/74 (mudança não afeta testes existentes, que não
  exercitam inferência real).

## 2026-09-02 — Teste real do SAM 3 no SMD: resultado e decisão

- **Resultado do pool completo (7.043 crops)**: cobertura média 0,527
  (SAM 1: 0,481), cobertura mínima 0,000 (SAM 1: 0,168), apenas 5 crops
  (0,07%) abaixo de 0,15 de cobertura.
- **Investigação dos 5 casos de cobertura zero**: 3 das 5 falhas vêm do
  mesmo vídeo (`MVI_1623_VIS`, mesmo `box_index=1`, frames 180/280/300) —
  provavelmente o mesmo objeto rastreado ao longo do vídeo, não 5 falhas
  independentes. Inspeção visual (caixa desenhada sobre a cena original)
  confirmou: todos os 3 casos verificados são objetos genuinamente
  minúsculos (19×18px a 43×24px) na borda extrema da imagem, no limite do
  que é visualmente distinguível do fundo de água mesmo a olho nu — não
  um defeito do SAM 3 nem do nosso código de correspondência por IoU.
- **Interpretação**: a salvaguarda de IoU (`indice_melhor_iou`) funcionou
  como projetado — quando nenhuma instância detectada corresponde de
  forma confiável à caixa de anotação, o resultado é cobertura zero
  (falha visível e auditável no manifesto), não uma máscara errada
  aceita silenciosamente. Comportamento preferível a uma segmentação
  ruim não sinalizada.
- **Decisão**: adotar `SegmentadorSAM3` como segmentador padrão para as
  quatro fontes deste projeto (SMD, SeaShips, ABOShips, UA-DETRAC),
  substituindo o `SegmentadorSAM` (SAM 1) usado no teste inicial. Ambos
  os pools do SMD (SAM 1 em `crops_sam/`, SAM 3 em `crops_sam3/`)
  permanecem no Drive para eventual comparação futura, mas `crops_sam3/`
  é o candidato a pool oficial deste projeto.

## 2026-09-02 — segmentador adicionado ao script do UA-DETRAC

- `scripts/preparar_ua_detrac.py` atualizado com o mesmo parâmetro opcional
  `segmentador` já presente nos outros três scripts de extração --
  repassado à chamada de `extrair_crops_de_yolo` na etapa de extração do
  pool de crops de veículo (split train deduplicado). Nenhuma mudança na
  lógica de colapso de classes ou materialização do split valid. Suíte
  completa: 74/74 (sem alteração de comportamento quando segmentador=None).

## 2026-09-02 — UA-DETRAC processado com SAM 3

- **Resultado**: 85.170 crops de veículo extraídos e segmentados com SAM 3
  a partir do split train deduplicado do UA-DETRAC-DATASET-10K, salvos em
  `EXPERIMENTO_ATRIBUICAO_CAUSAL/segundo_dominio_uadetrac_sam3/crops_veiculos/`.
  Fundo de composição (split valid, materializado e verificado) salvo em
  `.../valid_background/`.
- **Ainda não verificado**: qualidade da segmentação neste pool (cobertura
  média/mínima, casos de falha) — a mesma checagem já aplicada ao SMD
  (amostra aleatória + piores casos por cobertura) ainda não foi rodada
  aqui. Pendente antes de considerar este pool validado.
- **Restam**: SeaShips e ABOShips ainda não processados com SAM 3 (só com
  recorte retangular, na extração inicial da tarefa -1.6).

## 2026-09-02 — Bug corrigido: manifestos do UA-DETRAC não eram copiados para o Drive

- **Achado**: ao tentar inspecionar a qualidade da segmentação do
  UA-DETRAC, `manifesto_extracao_bruta_ua_detrac.csv` não foi encontrado
  no armazenamento local do Colab (`/content/ua_detrac_extraido_sam3/`).
- **Causa raiz**: `scripts/preparar_ua_detrac.py` nunca copiava os três
  manifestos (extração bruta, filtro de qualidade, metadata do filtro)
  para o Drive — diferente dos outros três scripts de extração
  (`extrair_smd.py`, `extrair_seaships.py`, `extrair_aboships.py`), que já
  faziam isso desde a tarefa -1.6. Como o armazenamento local do Colab
  (`/content/...`) não sobrevive a reinício/desconexão de sessão, esses
  manifestos ficaram irrecuperáveis assim que a sessão mudou — só os
  crops finais e o fundo de composição (copiados ao Drive) sobreviveram.
- **Correção**: `preparar_ua_detrac.py` agora copia os três manifestos
  para `destino_drive`, mesmo padrão dos outros três scripts.
- **Consequência prática**: os manifestos do processamento já concluído
  (85.170 crops) foram perdidos e não são recuperáveis — só os crops em
  si e o fundo de composição estão no Drive. Para ter o manifesto (e
  poder inspecionar cobertura_mascara, motivos de descarte, etc.), é
  necessário **rodar a extração do UA-DETRAC de novo**, agora com o
  script corrigido.
- Suíte completa: 74/74 (mudança não afeta nenhum teste existente).

## 2026-09-02 — Violação da própria convenção de armazenamento (§12.1): crops soltos no Drive causando I/O error

- **Erro observado**: `OSError: [Errno 5] Input/output error` ao tentar
  checar a existência de um arquivo de crop do UA-DETRAC em
  `crops_veiculos/` no Drive -- diferente de `FileNotFoundError` (arquivo
  ausente), este erro indica instabilidade do Google Drive montado via
  FUSE no Colab.
- **Causa raiz**: `crops_veiculos/` contém 85.170 arquivos PNG individuais
  soltos diretamente no Drive, e o total agregado das quatro fontes já
  passa de 100 mil arquivos soltos (SMD: 7.043; UA-DETRAC: 85.170;
  SeaShips e ABOShips ainda por processar). Isso **viola diretamente** a
  convenção já registrada em `docs/README_DRIVE.md` (§12.1 do plano): "um
  `.zip` por artefato pesado, não pastas soltas com muitos arquivos
  pequenos -- evita escrita arquivo-a-arquivo lenta e vulnerável a queda
  quando o Drive é montado via FUSE" -- lição herdada do projeto anterior,
  mas não aplicada na prática pelos scripts de extração deste projeto.
- **Mitigação imediata**: `drive.mount(force_remount=True)` -- erros de
  I/O do FUSE costumam ser transitórios e um remontagem resolve na maioria
  dos casos.
- **Correção estrutural pendente**: os scripts de extração
  (`extrair_smd.py`, `extrair_seaships.py`, `extrair_aboships.py`,
  `preparar_ua_detrac.py`) devem compactar a pasta de crops final num
  único `.zip` antes de finalizar, em vez de deixar os arquivos soltos no
  Drive -- aplicar retroativamente aos pools já gerados (SMD, UA-DETRAC) e
  corrigir os scripts para as próximas execuções (SeaShips, ABOShips).
  Ainda não implementado.

## 2026-09-02 — Investigação dos piores casos do UA-DETRAC: dois mecanismos de falha distintos

- **Cobertura no pool completo (85.170 crops)**: média 0,694, mínima
  0,000, 289 casos (0,34%) abaixo de 0,15 -- taxa maior que o SMD (0,07%),
  mas ainda pequena em termos absolutos.
- **Inspeção visual dos 6 piores casos (lendo direto do zip fonte, já que
  os arquivos locais da sessão de extração não sobreviveram)** revelou
  DOIS mecanismos de falha distintos, diferente do SMD (que tinha só um):
  1. **Objeto genuinamente minúsculo e isolado** (10×10px, avenida vazia)
     -- mesmo padrão benigno já visto no SMD.
  2. **Oclusão por densidade de cena**: a maioria dos piores casos (4 de
     6) vem de cenas de trânsito muito denso (interseção cheia, fila de
     carros colados), com caixas pequenas posicionadas onde veículos
     vizinhos se tocam -- ambiguidade de fronteira entre objetos, não
     apenas tamanho pequeno. Este mecanismo não existe do mesmo jeito no
     domínio marítimo (SMD).
  3. **Possível problema de qualidade de anotação**: um caso (104×94px,
     ônibus) tinha cobertura zero apesar de NÃO ser pequeno -- a caixa
     cobria apenas o teto/parte superior do veículo, não a silhueta
     completa. Levantado como suspeita, não confirmado sistematicamente
     (checagem pontual, não uma varredura completa do pool).
- **Achado metodológico relevante para a Fase 2.5**: a estrutura de
  dificuldade de segmentação difere entre os dois domínios de validação
  (SMD: objeto pequeno isolado; UA-DETRAC: objeto pequeno + oclusão por
  densidade) -- registrado como observação útil para a discussão de
  generalização do artigo, não como decisão a tomar agora.
- **Decisão**: pool do UA-DETRAC (SAM 3) aceito como está — taxa de falha
  baixa (0,34%) e explicável por mecanismos identificáveis, não uma falha
  sistemática do segmentador.

## 2026-09-02 — Correção estrutural: pools de crops compactados em .zip, não mais arquivos soltos no Drive

- **Entregue**: `src/extraction/archive_utils.py` -- `compactar_arquivos()`
  compacta uma lista específica de arquivos (só os crops MANTIDOS após o
  filtro de qualidade, não a pasta bruta inteira) num único `.zip`;
  `carregar_pool_de_crops_do_zip()` extrai de volta para uma pasta local e
  devolve a lista no formato `list[(fonte, caminho)]` que
  `src.compose.compor_dataset` já espera -- **nenhuma mudança** foi feita
  no componente de composição em si, conforme decidido.
- **Os quatro scripts de extração atualizados** (`extrair_smd.py`,
  `extrair_seaships.py`, `extrair_aboships.py`, `preparar_ua_detrac.py`):
  a etapa final agora compacta localmente e copia um ÚNICO arquivo `.zip`
  para o Drive, em vez de copiar milhares de arquivos individuais --
  correção pela raiz do problema de I/O (`OSError: Input/output error`)
  encontrado ao inspecionar o UA-DETRAC: a própria operação de copiar
  muitos arquivos pequenos ao Drive via FUSE é o que causa a instabilidade,
  não só o armazenamento posterior. Consistente com a convenção já
  registrada em `docs/README_DRIVE.md` (§12.1 do plano).
- **`valid_background` do UA-DETRAC permanece como pastas soltas**
  (decisão deliberada, não descuido): tem 500 imagens, ordem de grandeza
  bem menor que os pools de crops (7 mil a 85 mil), risco de I/O muito
  menor nessa escala -- não foi convertido para zip.
- **Ação necessária**: os pools já gerados e salvos como pastas soltas
  (`crops_sam3/smd/`, `segundo_dominio_uadetrac_sam3/crops_veiculos/`)
  precisam ser reprocessados com os scripts corrigidos, ou compactados
  manualmente, para eliminar o risco de I/O que já se manifestou uma vez.
- Coberto por `tests/test_archive_utils.py` (4 testes, incluindo o ciclo
  completo compactar→extrair→formato do pool, e combinação de múltiplas
  fontes num pool único). Suíte completa: 78/78 passando.

## 2026-09-02 — Segmentação com SAM 3 concluída nas quatro fontes

- **SeaShips**: 9.198 crops, compactados em `crops_sam3/seaships.zip`.
- **ABOShips**: 41.967 crops, compactados em `crops_sam3/aboships.zip`.
- **Contagens conferem exatamente** com a extração retangular original
  (tarefa -1.6, antes da segmentação) para as duas fontes — confirma que a
  segmentação SAM 3 não altera quantos crops passam pelo filtro unificado
  (`min_dim_px=1`, sem filtrar nada nesta rodada), só como cada crop é
  recortado/mascarado.
- **Estado final**: as quatro fontes de crops (SMD, SeaShips, ABOShips,
  UA-DETRAC) estão segmentadas com SAM 3, compactadas em `.zip` desde a
  origem (sem arquivos soltos no Drive), com manifesto de extração
  (incluindo `cobertura_mascara`) preservado para cada uma. Isso fecha a
  etapa de segmentação da Fase -1/tarefa -1.6.
- **Pendente, não bloqueante**: inspeção de qualidade (amostra + piores
  casos) ainda não foi feita para SeaShips e ABOShips, ao contrário de SMD
  e UA-DETRAC (já investigados). Recomendado antes de decidir `min_dim_px`
  definitivo na tarefa 0.2, mas não impede o início dessa tarefa.

## 2026-09-02 — Inspeção de qualidade do SeaShips: terceiro mecanismo de falha (folga de anotação)

- **Resultado do pool completo (9.198 crops)**: cobertura média 0,514,
  mínima 0,056 (nunca zero — diferente de SMD e UA-DETRAC), máxima 0,955.
  26 casos (0,28%) abaixo de 0,15 -- taxa intermediária entre SMD (0,07%)
  e UA-DETRAC (0,34%).
- **Padrão visual nos piores casos**: a maioria mostra DOIS objetos
  segmentados separados dentro do mesmo crop, com grande vão vazio entre
  eles -- terceiro mecanismo de falha, distinto dos já registrados para
  SMD (objeto minúsculo isolado) e UA-DETRAC (oclusão por densidade de
  cena). Interpretação: a caixa de anotação original do SeaShips, em
  vários casos, é larga/frouxa o suficiente para abranger a embarcação
  principal e um segundo objeto pequeno distante (outra embarcação,
  boia, estrutura de doca), com água vazia entre os dois -- o SAM 3
  segmenta corretamente um objeto dentro da caixa, mas a cobertura fica
  moderada porque a caixa em si não corresponde a um único objeto
  compacto.
- **Conexão direta com feature já planejada**: este padrão é exatamente o
  que a feature `folga_anotacao` (Família 3, §6 do plano) foi desenhada
  para capturar -- evidência visual concreta, antes mesmo do Estágio A
  rodar, de que "qualidade de anotação da fonte" é uma dimensão real e
  observável, não uma hipótese abstrata. Reforça a decisão já registrada
  de decompor "fonte" em `folga_anotacao`/`truncamento` para testar
  mediação no SHAP.
- **Decisão**: pool do SeaShips (SAM 3) aceito como está -- taxa de falha
  baixa e mecanismo bem identificado, não uma falha do segmentador.

## 2026-09-02 — Inspeção de qualidade do ABOShips: taxa de falha maior explicada pelo perfil de tamanho já conhecido da fonte

- **Resultado do pool completo (41.967 crops)**: cobertura média 0,615,
  mínima 0,000, máxima 1,000. 398 casos (0,95%) abaixo de 0,15 -- taxa
  maior que as outras três fontes (SMD 0,07%, SeaShips 0,28%, UA-DETRAC
  0,34%).
- **Descartada hipótese de inconsistência de anotação**: taxa de
  divergência entre `width`/`height` do CSV e a bbox derivada é 0,000
  tanto nas falhas quanto no resto -- não é problema de dado corrompido.
- **Causa confirmada**: as 167 falhas completas (cobertura=0) têm menor
  lado com mediana de 5px, máximo 17px -- todas abaixo de 20px. No pool
  inteiro, 38,3% das caixas têm menor lado <20px (consistente com o
  "66,3% <50px" já documentado no projeto anterior para esta fonte
  especificamente). Dessas caixas <20px, apenas 1,0% falha completamente
  (cobertura zero) -- a falha total é exceção mesmo dentro do subgrupo
  difícil, não a regra.
- **Interpretação**: a taxa de falha mais alta do ABOShips não é defeito
  do SAM 3 -- é consequência direta e já esperada do perfil de tamanho
  conhecido e registrado desta fonte (fração grande de objetos
  extremamente pequenos). Confirmação numérica nova de uma observação já
  registrada, não achado inédito.
- **Decisão**: pool do ABOShips (SAM 3) aceito como está.

## 2026-09-02 — Inspeção de qualidade concluída nas quatro fontes

| Fonte | Cobertura média | Abaixo de 0,15 | Mecanismo principal de falha |
|---|---|---|---|
| SMD | 0,481 | 0,07% | objeto minúsculo isolado |
| SeaShips | 0,514 | 0,28% | folga de anotação (caixa larga cobrindo 2 objetos) |
| UA-DETRAC | 0,694 | 0,34% | objeto pequeno + oclusão por densidade de trânsito |
| ABOShips | 0,615 | 0,95% | fração grande de objetos <20px (perfil conhecido da fonte) |

Todas as quatro fontes com segmentação SAM 3 aceita. Cada fonte revelou um
mecanismo de falha distinto e explicável -- nenhum indica defeito
sistemático do segmentador. Encerra a etapa de segmentação da Fase -1;
próximo passo é a tarefa 0.2 (perfis das quatro fontes, decisão de
`min_dim_px`).

## 2026-09-02 — Tarefa 0.2: perfilamento das fontes e tabela de decisão de min_dim_px

- **Entregue**: `src/profiling/source_profile.py` -- `perfilar_fonte()`
  lê os manifestos de extração já gerados (nenhum dado novo necessário) e
  calcula estatísticas descritivas do menor lado de cada crop por fonte;
  `tabela_decisao_min_dim_px()` monta uma tabela fonte × limiar candidato,
  mostrando quantos crops sobreviveriam em cada opção -- decisão do valor
  final permanece humana, informada pelo trade-off explícito, não
  calculada automaticamente.
- `scripts/perfilar_fontes.py` roda contra os três manifestos reais
  disponíveis no Drive (SMD, SeaShips, ABOShips -- UA-DETRAC fica de fora
  desta tabela porque não compete pelo mesmo `min_dim_px`: é fonte de um
  domínio de validação separado, com seu próprio filtro).
- Coberto por `tests/test_source_profile.py` (5 testes, incluindo um que
  simula duas fontes com perfis de tamanho bem diferentes e confirma que
  a tabela revela o trade-off sem escolher um número sozinha). Suíte
  completa: 83/83.
- **Ação pendente para você rodar no Colab**: executar
  `scripts/perfilar_fontes.py` para gerar a tabela real e decidir
  `min_dim_px` com base nela -- ainda não fiz isso, não tenho acesso ao
  Drive.

## 2026-09-02 — Correção: dataset_25k_v2.zip TEM anotação e pode ser fonte de crop do InaTechShips

- **Erro anterior corrigido**: em 2026-08-31, `dataset_25k_v2.zip` foi
  classificado como "fora de escopo" (assumido como o mesmo artefato do
  experimento de pré-treino direto do artigo original -- imagens inteiras
  sem anotação de caixa). Essa conclusão foi tomada **sem verificar
  anotação**, e estava incompleta.
- **Achado real**: o zip contém `reconstrucao_report.json` documentando
  que `dataset_25k_v2` é uma reconstrução posterior de
  `InaTechShips/dataset_25k` -- reorganizada em splits train/val/test
  (60/20/20, seed 42), com **anotação YOLO já presente**, incluindo
  `labels_single_class/` já preparado. 27.796 imagens únicas, 10 classes
  originais de tipo de embarcação.
- **Decisão revisada**: `dataset_25k_v2.zip` é candidato real a fonte de
  crop do InaTechShips (pendência sinalizada anteriormente e nunca
  resolvida). Formato YOLO já verificado como compatível com o extrator
  já existente (`extrair_crops_de_yolo`) -- se confirmado no exame
  detalhado, nenhum extrator novo é necessário, mesmo padrão de
  reaproveitamento já usado para SMD e UA-DETRAC.
- **Lição de método**: esta correção reforça a prática de nunca
  classificar um artefato como "fora de escopo" sem verificar
  explicitamente a presença/ausência de anotação -- a classificação
  anterior foi feita por inferência de nome/contexto, não por inspeção
  direta do conteúdo.

## 2026-09-02 — InaTechShips confirmado: formato YOLO, 27.796 imagens, estrutura diferente das outras três fontes

- **Estrutura confirmada**: `dataset_25k_v2.zip`, splits train/val/test
  (16.677/5.558/5.561, disjuntos por id, checagem de disjunção já presente
  no relatório de reconstrução). YOLO, `labels_single_class/` já pronto
  (10 classes originais de tipo de navio colapsadas para `embarcacao`).
- **Achado estrutural**: a caixa de anotação de amostra cobre ~92% de
  largura e ~59% de altura da imagem -- sugere que o InaTechShips é
  composto de fotos de close-up de navio único (estilo catálogo/spotting),
  não cenas de vigilância com objetos pequenos e distantes como SMD,
  SeaShips e ABOShips. Implicação esperada: crops desta fonte devem ser
  tipicamente maiores e com mais detalhe visual que as outras três --
  contribuição de diversidade genuína ao pool, não um problema.
- **Decisão**: nenhum extrator novo necessário -- reaproveita
  `extrair_crops_de_yolo` (já usado para SMD e UA-DETRAC). Como é fonte de
  crop pura (não tem papel de alvo/fundo de composição), as três divisões
  (train/val/test) serão combinadas num único pool, maximizando volume
  (sem risco de memorização, que só se aplica ao dataset-alvo).

## 2026-09-02 — Entregue: script de extração do InaTechShips (quarta fonte de crop)

- `scripts/extrair_inatechships.py`: extrai `dataset_25k_v2.zip`, roda
  `extrair_crops_de_yolo` três vezes (train/val/test, sem novo código),
  combina os manifestos de cobertura dos três splits antes de aplicar o
  filtro unificado sobre o pool combinado, e compacta o resultado num
  único `crops_sam3/inatechships.zip` -- mesma convenção de armazenamento
  já corrigida para as outras três fontes.
- `min_dim_px=20` já incorporado como valor de exemplo no docstring do
  script, refletindo a decisão fechada na tarefa 0.2.
- Suíte completa (sem alteração): 83/83 -- este script, como os outros
  três de ponta a ponta, depende de zip real e não tem teste unitário
  próprio (mesmo padrão já estabelecido).
- **Ação pendente para você rodar no Colab**: executar o script com
  `segmentador=segmentador_sam3` -- ainda não fiz isso, não tenho acesso
  ao Drive.

## 2026-09-02 — InaTechShips extraído com SAM 3 (27.733 crops) e tabela de decisão atualizada para quatro fontes

- **Resultado da extração**: 27.796 crops extraídos (train+val+test
  combinados), 27.733 mantidos após o filtro `min_dim_px=20` (99,8% de
  aproveitamento) -- taxa de perda quase nula, consistente com o achado
  estrutural já registrado (caixas grandes cobrindo quase o quadro
  inteiro, poucas caixas caem abaixo de 20px nesta fonte).
- **`src/profiling/source_profile.py` estendido**: `perfilar_fonte()`
  agora aceita um único manifesto OU uma lista de manifestos (necessário
  porque o InaTechShips foi extraído em três manifestos separados, um por
  split, diferente das outras três fontes que geram um manifesto único).
  Retrocompatível -- chamada com um único caminho continua funcionando
  sem alteração. `scripts/perfilar_fontes.py` atualizado para incluir o
  InaTechShips (lista dos três manifestos) na tabela de decisão.
- Coberto por 1 teste novo (`test_perfilar_fonte_aceita_lista_de_multiplos_manifestos`).
  Suíte completa: 84/84.
- **Ação pendente para você rodar no Colab**: re-executar
  `scripts/perfilar_fontes.py` para gerar a tabela de decisão com as
  QUATRO fontes reais, confirmando se `min_dim_px=20` continua sendo a
  escolha certa agora que o InaTechShips está incluído.

## 2026-09-02 — Tabela de decisão de min_dim_px confirmada com as quatro fontes reais

- **Decisão `min_dim_px=20` confirmada**: SMD 94,8%, SeaShips 96,4%,
  ABOShips 61,7% (único custo real), InaTechShips 99,8% mantidos.
  Nenhuma mudança em relação à decisão feita com 3 fontes.
- **Achado adicional -- disparidade de escala nativa entre fontes**:
  mediana do menor lado por fonte -- SMD 54px, SeaShips 73px, ABOShips
  27px, **InaTechShips 358px** (mais de 6× maior que qualquer outra
  fonte). Consistente com a caracterização já registrada (InaTechShips =
  fotos de close-up de navio único, não cenas de vigilância com objetos
  pequenos e distantes).
- **Relevância metodológica**: como a escala do dataset-alvo (CITRA-3D-Real,
  perfil da tarefa 0.1) é muito mais próxima da escala do
  SMD/SeaShips/ABOShips do que da do InaTechShips, colagens usando crops
  do InaTechShips vão exigir fator de reescala tipicamente muito mais
  agressivo (redução maior) que colagens das outras três fontes. Isso
  reforça, com evidência numérica concreta, a decisão já registrada de
  tratar `fator_reescala` (Família 2, §6 do plano) como feature própria a
  medir por colagem, em vez de confiar em "identidade da fonte" como
  preditor direto -- exatamente o tipo de confound que o desenho do
  Estágio A já foi construído para evitar.
- **Tarefa 0.2 concluída.**

## 2026-09-02 — Tarefa 0.3: verificação de cobertura do reservatório para o fatorial

- **Entregue**: `src/profiling/coverage_check.py` -- `obter_tamanhos_absolutos_alvo()`
  lê os labels YOLO do dataset-alvo e retorna a lista bruta de dimensões
  absolutas de caixa (mesma lógica de conversão de `target_profile.py`,
  aqui sem agregação, para permitir amostragem individual);
  `simular_compatibilidade_escala()` simula pareamentos aleatórios
  (crop de uma fonte × caixa de destino real) e classifica cada um por
  `fator_reescala` resultante (mesma fórmula usada em `src/compose/compose.py`)
  em "casada" (faixa configurável, padrão [0,5, 2,0]), "descasada_downscale"
  ou "descasada_upscale".
- **Teste central** (`test_fonte_com_crops_muito_maiores_que_destino_produz_maioria_downscale`):
  reproduz em miniatura, com números sintéticos no mesmo padrão do
  InaTechShips real (crops ~400px vs. destino ~30px), e confirma
  numericamente (>90% descasada_downscale, <10% casada) o risco que
  havíamos identificado por raciocínio antes de rodar contra dados reais.
- `scripts/verificar_cobertura_fatorial.py` roda a simulação real:
  tamanhos de destino lidos do split de treino do CITRA-3D-Real
  (`labels_final`, maior amostra disponível), tamanhos de origem lidos dos
  manifestos de filtro de qualidade já gerados (crops que passaram
  `min_dim_px=20`) das quatro fontes.
- Coberto por `tests/test_coverage_check.py` (5 testes). Suíte completa:
  89/89.
- **Ação pendente para você rodar no Colab**: executar
  `scripts/verificar_cobertura_fatorial.py` -- ainda não fiz isso, não
  tenho acesso ao Drive. Se o InaTechShips confirmar `pct_casada` muito
  baixo com dados reais (como a hipótese sugere), será necessário decidir
  como o Estágio B vai lidar com isso antes da Fase 3 -- opções a discutir
  então: excluir InaTechShips da célula "casada" (aceitando desbalanceamento
  documentado), ou restringir a amostragem de destino usada nessa célula a
  um subconjunto de caixas do CITRA compatível com o tamanho nativo do
  InaTechShips.

## 2026-09-02 — Tarefa 0.3 concluída: decisão sobre assimetria de fonte na célula "escala casada"

- **Confirmado com dados reais**: SMD 23,0%, SeaShips 18,1%, ABOShips
  21,4%, **InaTechShips 0,75%** de pareamentos "casados" (fator_reescala
  entre 0,5 e 2,0), simulados contra as caixas reais do split de treino
  do CITRA-3D-Real (20.000 amostras por fonte, 4.489 caixas de destino).
- **Decisão fechada** (opção 1 do conjunto de alternativas + espírito da
  opção 3): InaTechShips excluído da célula "escala casada" do fatorial;
  participa plenamente da célula "escala descasada" (99,0% de
  aproveitamento). SMD, SeaShips e ABOShips participam de ambas as
  células, balanceados entre si. Assimetria pré-registrada e reportada
  como achado substantivo -- o InaTechShips é, por natureza, incompatível
  de escala com o alvo -- não escondida como limitação.
- **Registrado em três lugares**: (1) `docs/PLANO_v2_atribuicao_causal_composicao_sintetica.md`,
  §5.7, com a justificativa completa; (2) este changelog; (3)
  `configs/fontes_por_nivel_escala.json`, artefato de configuração que a
  Fase 3 (construção real das células do fatorial) vai consumir --
  codifica a decisão para que não dependa de memória da equipe quando
  chegar a hora de implementar.
- **Tarefa 0.3 concluída.** Restam na Fase 0: 0.4 (gerar colagens de
  sondagem sobre o split de validação), 0.5 (redigir e commitar as
  previsões), 0.6 (lacrar o commit de pré-registro).

## 2026-09-02 — Tarefa 0.4: script de geração das colagens de sondagem

- `scripts/gerar_colagens_sondagem.py`: combina o pool de crops das quatro
  fontes (extração local dos quatro zips via `carregar_pool_de_crops_do_zip`,
  já existente desde a correção de armazenamento), e chama
  `src.compose.compor_dataset` sobre o split de **validação** do
  CITRA-3D-Real -- nenhuma mudança no componente de composição foi
  necessária, apenas montagem do pool combinado antes da chamada.
- **`n_variacoes=13` proposto, não decidido unilateralmente**: mesmo valor
  do projeto anterior, mas registrado explicitamente como proposta a
  confirmar, não herança tácita -- como a composição não usa GPU, o custo
  de aumentar esse número é de espaço/tempo de geração, não de cota de
  GPU, e vale a equipe decidir com esse trade-off em mente.
- Resultado esperado, com 332 imagens de validação e 1.267 boxes (perfil
  já medido na tarefa 0.1): ~16.470 colagens (linhas de manifesto), ~4.316
  imagens de cena completa geradas, compactadas em `colagens_images.zip` +
  `colagens_labels.zip` antes de ir ao Drive.
- **Ação pendente para você rodar no Colab**: executar
  `scripts/gerar_colagens_sondagem.py` -- ainda não fiz isso, não tenho
  acesso ao Drive.

## 2026-09-02 — Correção: n_variacoes=13 não tinha justificativa válida para a tarefa 0.4

- **Erro identificado**: ao propor `n_variacoes=13` para as colagens de
  sondagem (tarefa 0.4), a justificativa dada foi "compatibilidade com o
  piso de referência já conhecido" -- sem verificar se a razão original
  do número 13 se aplicava ao novo contexto.
- **Origem real do 13, localizada em `write_balanced_trainlist` (projeto
  anterior)**: o número foi escolhido para equilibrar volume de dados
  50/50 entre imagens reais e sintéticas no braço de treino "joint"
  (real repetido 13× + sintético 1× = 17.524 + 17.524) -- uma
  preocupação de balanceamento de TREINO SUPERVISIONADO COM GPU.
- **Por que não se aplica aqui**: as colagens de sondagem do Estágio A
  não treinam nenhum modelo -- servem só para gerar o alvo binário
  (inferência com detector já treinado) e alimentar o GBM+SHAP. Não há
  "braço joint" nem necessidade de equilíbrio real/sintético 50/50 neste
  contexto. A justificativa original resolve um problema que não existe
  aqui.
- **Decisão corrigida**: `n_variacoes` para a tarefa 0.4 deve ser
  escolhido por raciocínio próprio deste contexto (mais variações por
  grupo geométrico ajudam a desemaranhar efeito de crop de efeito de
  geometria, sem custo de GPU envolvido na composição em si), não por
  herança do valor usado para outro propósito. Nenhuma análise de poder
  formal foi feita para determinar um valor ótimo -- pendente, análogo à
  análise de poder já reservada para a Fase 1.
- **Nenhum dano feito**: o script `gerar_colagens_sondagem.py` ainda não
  foi executado contra dados reais quando este erro foi identificado.

## 2026-09-02 — n_variacoes fechado em 20, com justificativa própria documentada no código

- `scripts/gerar_colagens_sondagem.py` atualizado: `n_variacoes=20` como
  padrão, com a justificativa correta (mais resolução para o Estágio A,
  sem custo de GPU) documentada diretamente no docstring da função --
  explicitamente marcada como não-herdada do valor 13 do projeto
  anterior, e como revisável se a Fase 2 mostrar necessidade.
- Volume esperado revisado: 332 imagens de val × 20 = 6.640 cenas
  geradas; 1.267 caixas × 20 ≈ 25.340 linhas de manifesto (colagens).
- Suíte completa: 89/89 (sem novo teste -- mudança de valor padrão em
  script de integração, mesmo padrão dos demais).

## 2026-09-02 — Tarefa 0.4 concluída: colagens de sondagem geradas

- **Resultado**: 25.340 colagens (linhas de manifesto) geradas sobre o
  split de validação do CITRA-3D-Real, combinando o pool das quatro
  fontes (85.941 crops carregados: SMD 7.043, SeaShips 9.198, ABOShips
  41.967, InaTechShips 27.733).
- **Checagem de consistência**: 25.340 = 1.267 caixas × 20 variações,
  exatamente como previsto -- confirma que o componente de composição
  está se comportando conforme o design.
- Imagens, labels e manifesto compactados e salvos em
  `estagio_a/colagens_sondagem_val/` no Drive.
- **Tarefa 0.4 concluída.** Restam na Fase 0: 0.5 (redigir e commitar as
  previsões) e 0.6 (lacrar o commit de pré-registro).

## 2026-09-02 — Tarefa 0.5: previsões pré-registradas redigidas

- **Entregue**: `docs/pre_registro/previsoes_fase0.md` -- sete previsões
  específicas e falseáveis (P1-P7), cada uma com critério explícito de
  confirmação e de refutação, cobrindo: ranking SHAP esperado do Estágio A
  (P1-P4), efeito principal esperado do Estágio B (P5-P6), e replicação do
  mecanismo no segundo domínio de validação (P7).
- Previsões derivadas dos achados já medidos nesta sessão (não
  inventadas): perfil do alvo (0.1), perfis das fontes (0.2), assimetria
  de escala do InaTechShips (0.3), padrão de folga de anotação do
  SeaShips e perfil de tamanho do ABOShips (inspeções de qualidade da
  segmentação).
- Documento explicita, em §5, o que **não** é previsto -- consistente com
  os limites já declarados no plano (§11).
- **Tarefa 0.5 concluída.** Resta na Fase 0: 0.6 (lacrar o commit de
  pré-registro).

## 2026-09-02 — Tarefa 0.6: script de lacração do pré-registro

- `scripts/lacrar_pre_registro.py`: calcula hash SHA-256 de cada artefato
  citado no documento de previsões (`perfil_citra_3d_real.json`,
  `tabela_min_dim_px.json`, `cobertura_fatorial.json`,
  `manifesto_colagens_sondagem_val.csv`), grava em `pre_registro/hashes.json`
  no Drive -- permite verificação futura de que os números citados nas
  previsões não foram alterados depois do commit de lacração.
- Suíte completa: 89/89 (script utilitário, sem lógica testável além de
  hash de arquivo, mesmo padrão de outros scripts de I/O simples).
- **Ação pendente para você**: (1) rodar `scripts/lacrar_pre_registro.py`
  no Colab; (2) copiar o `hashes.json` gerado para
  `docs/pre_registro/hashes.json` no repositório; (3) fazer o commit final
  que lacra a Fase 0 -- previsões + hashes juntos, no mesmo commit,
  seguido de push para o repositório público (garantindo o carimbo de
  tempo externo verificável, §0 do plano).
- **Isso encerra a Fase 0.** Próxima etapa do cronograma: Fase 1 (piloto
  do protocolo de treino V2 -- primeira etapa que exige GPU de treino
  neste projeto).

## 2026-09-02 — Início da Fase 1: montador de trainlist balanceado, reescrito e testado

- **Distinção explícita registrada**: `n_variacoes=13` foi rejeitado na
  tarefa 0.4 (colagens de sondagem do Estágio A) porque a justificativa
  original (equilíbrio real/sintético 50/50 num braço de treino com GPU)
  não se aplicava -- nenhum treino ocorre sobre aquelas colagens. Aqui, na
  Fase 1, a mesma justificativa **se aplica de verdade**: estamos
  montando o braço de treino real. Reaproveitar 13 nesta fase é
  verificado, não herdado às cegas.
- **Entregue**: `src/train/trainlist.py` -- `construir_trainlist_balanceado()`
  (real repetido N vezes + sintético 1 vez, formato de lista de caminhos
  consumível pelo `train:` de um data.yaml Ultralytics) e
  `construir_trainlist_real_sobreamostrado()` (braço de controle: real
  repetido pelo MESMO fator do braço sintético, zero sintéticos --
  isolando o efeito da repetição do efeito da composição, §5.7 do plano).
  Reescrito do zero neste projeto, não importa código do projeto
  anterior.
- Coberto por `tests/test_trainlist.py` (4 testes, incluindo reprodução
  proporcional do cenário real de 50/50 com `repeat_real=13`). Suíte
  completa: 93/93.
- **Próximo passo da Fase 1**: gerar as sintéticas de treino de verdade
  (composição sobre o split de TREINO do CITRA, com
  `permitir_split_treino=True` explícito, combinando o pool das quatro
  fontes) e escrever o script que invoca o treino Ultralytics YOLO
  (`yolo11n.pt`, confirmado pelo usuário) para os três braços × 3 seeds.

## 2026-09-02 — Fase 1: script de geração das sintéticas de treino

- `scripts/gerar_sinteticas_treino.py`: compõe sobre o split de TREINO do
  CITRA-3D-Real, com `permitir_split_treino=True` explícito -- uso
  legítimo aqui (geração de dado de treino), diferente do Estágio A
  (colagens de sondagem, que usam val justamente para não tocar treino).
  Combina o pool das quatro fontes, `n_variacoes=13` (verificado como
  aplicável neste contexto, ver entrada anterior).
- Resultado esperado: 1.348 imagens de treino × 13 = 17.524 imagens
  sintéticas de cena completa, volume compatível com o balanceamento
  50/50 via `construir_trainlist_balanceado(repeat_real=13)`.
- Compactado em `sinteticas_images.zip` + `sinteticas_labels.zip` antes de
  ir ao Drive, mesma convenção de armazenamento já corrigida.
- Suíte completa: 93/93 (sem novo teste unitário -- script de integração
  dependente de dado real, mesmo padrão dos demais).
- **Ação pendente para você rodar no Colab**: executar o script -- ainda
  não fiz isso, não tenho acesso ao Drive. Depois de gerado, os dois zips
  precisam ser extraídos para pastas locais antes de montar as trainlists
  (Ultralytics exige arquivos soltos em disco, não dentro de zip).

## 2026-09-02 — Sintéticas de treino geradas (Fase 1)

- **Resultado**: 17.524 imagens sintéticas de cena completa geradas sobre
  o split de treino do CITRA-3D-Real (58.357 colagens/linhas de
  manifesto), a partir do pool combinado das quatro fontes (85.941 crops).
- **Checagem de consistência**: 17.524 = 1.348 imagens de treino × 13
  variações, exatamente como previsto -- confirma que o balanceamento
  50/50 planejado (`repeat_real=13`) vai funcionar sem ajuste.
- Compactado em `sinteticas_images.zip` + `sinteticas_labels.zip`,
  salvos em `fase1_piloto/sinteticas_treino/` no Drive.

## 2026-09-02 — Fase 1: script de preparação local dos dados de treino

- **Motivo**: o treino lê cada imagem do trainlist uma vez por época --
  com centenas de épocas, isso significa centenas de milhares de leituras.
  Ler repetidamente do Drive via FUSE seria lento e sujeito ao mesmo tipo
  de instabilidade de I/O já documentado (OSError do UA-DETRAC). Solução:
  copiar tudo para disco local do Colab UMA VEZ antes do treino comecar --
  diferente do caso de armazenamento (onde zipar resolve), aqui o
  problema é leitura repetida durante o treino, que exige cópia local, não
  compactação.
- **Entregue**: `scripts/preparar_dados_locais_fase1.py` -- copia
  imagens/labels reais do CITRA (train+val) e extrai as sintéticas de
  treino para disco local; monta as três trainlists (B2, A_joint,
  controle) via `construir_trainlist_balanceado`/`construir_trainlist_real_sobreamostrado`
  (`repeat_real=13`); grava um `data.yaml` por braço, apontando `val:`
  sempre para o mesmo split de validação real (nunca sintético).
- Suíte completa: 93/93 (script de integração, sem teste unitário
  próprio, mesmo padrão dos demais scripts dependentes de dado real).
- **Próximo passo**: escrever o script que efetivamente invoca
  `YOLO(...).train(...)` para os três braços × seeds, usando
  `ProtocoloTreinoV2`/`gerar_kwargs_treino` já existentes -- ainda não
  temos os valores finais de `epochs_total`/`epoca_checkpoint`/
  `warmup_steps_alvo`, que são exatamente o que esta piloto deve revelar.

## 2026-09-02 — Fase 1: script de treino real (Ultralytics YOLO)

- `scripts/treinar_piloto_fase1.py`: invoca `YOLO(...).train(...)` para os
  três braços (B2, A_joint, controle) × 3 seeds (42, 123, 2024) --
  primeira etapa deste projeto que exige GPU de treino.
- **`epoca_checkpoint` usado como placeholder** (última época) --
  documentado explicitamente no código como não sendo a decisão final:
  a piloto existe para observar a curva de validação e decidir esse valor
  depois, não para assumi-lo antes.
- **`epochs_total=150`** proposto e justificado com base em achados
  parafraseados do histórico do projeto anterior (não copiados
  verbatim): braços com sintético convergem muito rápido (pico observado
  entre épocas 7-11 num teste específico) e depois degradam lentamente;
  o baseline puro precisa de orçamento bem maior (~140 épocas registradas
  no protocolo V2 anterior). 150 cobre a convergência esperada do
  baseline com margem, e permite observar diretamente (não assumir) o
  mesmo padrão de pico-e-degradação nos braços com sintético, usando
  dados próprios deste projeto.
- **`deterministic=True`** adicionado explicitamente à chamada de
  `.train()` -- exigido pelo portão de determinismo (§9 do plano).
- Suíte completa: 93/93 (script de treino real, sem teste unitário --
  depende de GPU e Ultralytics instalado, mesmo padrão dos demais scripts
  de execução real).
- **Ação pendente para você rodar no Colab**: instalar `ultralytics` se
  ainda não estiver, e executar o script -- esta é a primeira etapa que
  realmente vai consumir a GPU confirmada disponível. Recomendo rodar
  primeiro o portão de determinismo (mesmo braço/seed duas vezes) antes
  do sweep completo de 9 treinos, para não gastar GPU num pipeline
  potencialmente não-determinístico.

## 2026-09-09 — Portão de determinismo APROVADO (Fase 1)

- **Teste**: braço B2, seed 42, duas execuções completas (150 épocas,
  `deterministic=True`), em pastas de saída separadas
  (`determinismo_run1`, `determinismo_run2`).
- **Resultado**: comparação numérica direta dos dois `results.csv`
  (não apenas inspeção visual do log) confirma que todas as colunas de
  métrica e perda (`train/box_loss`, `train/cls_loss`, `train/dfl_loss`,
  `metrics/precision(B)`, `metrics/recall(B)`, `metrics/mAP50(B)`,
  `metrics/mAP50-95(B)`, `val/*_loss`, `lr/pg*`) são **numericamente
  idênticas** nas 150 épocas entre as duas execuções. Só a coluna `time`
  (relógio de parede, não faz parte do cálculo) diverge -- esperado, não
  é uma violação de determinismo.
- **Validação por comparação de arquivo, não de log**: optou-se por
  carregar os dois `results.csv` e comparar programaticamente
  (`df1.equals(df2)` + diff coluna a coluna) em vez de confiar na
  similaridade visual do log de console -- prática mais rigorosa,
  detecta divergências que passariam despercebidas a olho.
- **Portão aprovado.** Segue para a medição do piso de ruído (3 seeds do
  braço B2: 42 já disponível via `determinismo_run1`, faltam 123 e 2024).
- **Dado adicional já disponível como subproduto**: cada execução de B2
  levou ~0,41h (~24,6 min) -- rápido, dado que B2 é o braço com menos
  imagens por época (1.348) dos três.

## 2026-09-09 — Perda de dados por desconexão de sessão + correção do pipeline

- **Incidente**: a sessão do Colab desconectou após os três treinos de B2
  (seeds 42, 123, 2024) -- `/content/` voltou ao estado padrão, `fase1_runs/`
  e `fase1_dados_locais/` perdidos. Nenhum resultado tinha sido copiado
  para o Drive (só os dados de entrada -- sintéticas, colagens -- tinham
  essa proteção; os resultados de TREINO nunca tinham).
- **Recuperação parcial**: os logs de console de cada treino (colados na
  conversa) preservam as métricas por época impressas -- nenhum dado foi
  perdido de forma irrecuperável, mas a extração ficou mais arriscada
  (transcrição manual de texto longo, sujeita a erro) em vez de leitura
  direta de `results.csv`.
- **Correção aplicada**: `treinar_um_braco()` em `scripts/treinar_piloto_fase1.py`
  agora copia `results.csv`, `args.yaml` e os pesos (`best.pt`, `last.pt`)
  para o Drive ao final de cada execução -- mesma proteção que já
  existia para os dados de entrada, agora estendida aos resultados de
  treino. Aplica-se a todos os treinos futuros (as 6 execuções restantes
  do piloto: A_joint e controle × 3 seeds).
- **Leitura preliminar dos três B2 (via "Validating .../best.pt", números
  de baixo risco de transcrição -- linha única por execução)**: recall
  (`metrics/recall(B)`) = 0,690 (seed 42), 0,685 (seed 123), 0,695
  (seed 2024). **Ressalva importante**: esses números vêm do checkpoint
  `best.pt`, selecionado automaticamente pelo Ultralytics por critério de
  fitness baseado em validação -- isso é, na prática, seleção de
  checkpoint informada pelo val, exatamente o que o protocolo V2 (§3 do
  plano) determina evitar. Não deve ser usado como o cálculo formal do
  piso de ruído -- serve só como primeira leitura informal.
- **Decisão**: re-executar os três seeds de B2 com o script corrigido,
  em vez de confiar em transcrição manual do log ou nos números de
  `best.pt` -- custo baixo (~25 min cada) frente ao risco de comprometer
  o cálculo formal do piso de ruído com dado transcrito à mão ou
  metodologicamente inconsistente com o protocolo.

## 2026-09-09 — Piso de ruído do B2 calculado (Fase 1)

- **Operacionalização das "duas larguras de banda" (§9 do plano, antes
  vaga, agora definida com precisão e reprodutível)**:
  - **Banda 1 (ponto único)**: recall na época 150 (última, mesma do
    placeholder de `epoca_checkpoint`). Mede ruído no caso mais sensível
    a flutuação de uma única época.
  - **Banda 2 (janela suavizada)**: média do recall nas últimas 10 épocas
    (141-150) de cada seed. Suaviza flutuação época-a-época dentro de
    cada seed antes de comparar entre seeds.
- **Resultado (3 seeds de B2: 42, 123, 2024, dados reais de `results.csv`
  recuperados do Drive)**:
  - Banda 1: média 0,6883, desvio padrão 0,0078, amplitude (max-min)
    0,0150 (1,50 pp).
  - Banda 2: média 0,6889, desvio padrão 0,0062, amplitude 0,0121
    (1,21 pp).
- **Concordância entre bandas**: as duas medições convergem razoavelmente
  (0,62-0,78 pp de desvio padrão) -- não é uma medição instável que muda
  drasticamente conforme o critério.
- **Regra de leitura estabelecida para as fases seguintes (§7 do plano)**:
  um efeito medido na Fase 3 só deve ser tratado como real se o delta
  observado for maior que ~1,5 pp (banda 1, mais conservadora) -- deltas
  menores não são distinguíveis de flutuação de seed neste protocolo.
- **Próximo passo**: rodar A_joint e controle × 3 seeds cada (6 execuções
  restantes do piloto), com o script já corrigido para salvar no Drive.

## 2026-09-09 — Piloto da Fase 1 completo: as 9 execuções verificadas

- **Verificação rigorosa aplicada**: em vez de checar apenas a existência
  de `results.csv` (checagem anterior, insuficiente -- um treino
  interrompido no meio também gera um `results.csv`, só que parcial), a
  verificação final conferiu explicitamente a última época registrada em
  cada arquivo e a presença de `weights/last.pt`/`weights/best.pt`.
- **Resultado**: as 9 execuções (B2, A_joint, controle × seeds 42, 123,
  2024) completaram as 150 épocas integralmente, com pesos finais
  presentes. Nenhuma execução parcial remanescente.
- **Piloto da Fase 1 tecnicamente completo.** Próximo passo: análise das
  curvas de validação (recall por época) dos três braços, para (1)
  confirmar ou refutar o padrão de pico-precoce-e-degradação previsto
  para os braços com repetição/sintético, (2) decidir o `epoca_checkpoint`
  real do protocolo (substituindo o placeholder), e (3) calcular o piso
  de ruído dos outros dois braços (A_joint, controle), não só do B2.

## 2026-09-09 — Decisão fechada: epoca_checkpoint = 150 (todos os braços)

- **Análise das 9 curvas de validação (B2, A_joint, controle × 3 seeds)**:
  confirma o mecanismo previsto (braços com mais imagens/época convergem
  muito mais rápido -- A_joint pico em 21-39, controle em 55-84, B2 só em
  108-141) e o padrão de pico-e-degradação (A_joint cai 2-4pp do pico até
  a época 150; controle cai 1,5-2pp; B2 cai apenas 1-1,7pp).
- **Achado que exige cautela, não conclusão precipitada**: `controle`
  (real repetido, sem sintético) supera `A_joint` (com sintético) no pico
  e na época final, nas três seeds. Isso NÃO é evidência de que
  composição sintética piora o resultado -- esta piloto usa o pool
  inteiro sem separar por condição de escala (tarefa 0.3 já mediu que a
  maioria dos pareamentos do pool cai em "escala descasada": SMD 58,9%,
  SeaShips 70,2%, ABOShips 32,0-46,6%, InaTechShips 99,0%). O `A_joint`
  desta piloto testa majoritariamente a condição já suspeita de ser
  desfavorável, diluída numa média -- exatamente o que o fatorial da
  Fase 3 existe para desembaraçar. Nenhuma conclusão sobre o valor da
  composição sintética deve ser tirada desta piloto.
- **Decisão fechada**: `epoca_checkpoint = 150` (época final do
  cronograma, epochs_total), a MESMA para os três braços. Justificativa:
  qualquer época intermediária "otimizada por braço" reintroduziria
  seleção de checkpoint informada por comportamento de validação,
  favorecendo estruturalmente os braços que convergem tarde (B2) -- a
  época final é a única opção que não exige nenhuma escolha ad-hoc por
  braço, e a degradação que ela captura nos braços com sintético é parte
  real do fenômeno em estudo, não algo a esconder escolhendo um "ponto
  bonito" no meio do caminho.
- **Implicação operacional direta**: a partir de agora, toda análise
  formal de resultado usa `weights/last.pt` (pesos da época 150) de cada
  execução -- nunca `weights/best.pt` (seleção automática do Ultralytics
  por critério de fitness informado por validação, que o protocolo V2
  já proíbe usar como base de decisão, §3 do plano).
- **Piso de ruído do B2 (já calculado)** permanece válido como régua de
  referência (banda 1: 1,50pp; banda 2: 1,21pp) -- calculado exatamente
  na época 150, coerente com a decisão agora fechada.
- **Isso encerra a análise central da Fase 1.** Pendente: calcular o
  piso de ruído (mesmas duas bandas) para A_joint e controle também, para
  completude, antes de considerar a Fase 1 totalmente fechada.

## 2026-09-09 — Fase 1 concluída: piso de ruído consolidado dos três braços

- **Piso de ruído por braço** (banda 1 / banda 2, desvio padrão e
  amplitude max-min entre as 3 seeds, na época 150):
  - B2: desvio 0,0078/0,0062, amplitude 0,0150/0,0121.
  - A_joint: desvio 0,0103/0,0108, amplitude 0,0201/0,0192.
  - controle: desvio 0,0099/0,0103, amplitude 0,0182/0,0186.
- **Regra de leitura revisada**: o piso de ruído do B2 isolado (~1,5pp,
  usado provisoriamente antes) subestima o ruído real dos braços do tipo
  joint/composição, que é o que a Fase 3 vai comparar. A régua
  conservadora correta, usando a maior amplitude observada entre os três
  braços, é **~2,0 pp** (A_joint, banda 1). Um efeito medido na Fase 3
  só deve ser tratado como real se superar essa margem -- substitui a
  estimativa de 1,5pp registrada anteriormente.
- **Fase 1 concluída** com todos os portões passados: determinismo
  aprovado (comparação numérica exata de B2/seed42, duas execuções);
  piso de ruído medido nos três braços, duas bandas cada;
  `epoca_checkpoint=150` fechado como decisão definitiva do protocolo,
  aplicável uniformemente aos três braços em todas as fases seguintes.
- **Próxima fase do cronograma: Fase 2 (Estágio A)** -- rodar os
  detectores já treinados nesta piloto sobre as 25.340 colagens de
  sondagem geradas na tarefa 0.4 (Fase 0), gerar o alvo binário de
  acerto/erro por caixa, construir a tabela de features, e treinar o
  modelo substituto (gradient boosting) com SHAP.

## 2026-09-14 — Início da Fase 2 (Estágio A): decisão do gerador do alvo e script da passada única de GPU

- **Decisão confirmada**: o alvo binário (acerto/erro por caixa colada,
  IoU >= 0,5) é gerado pelos 3 checkpoints de **B2** (seeds 42, 123, 2024,
  `weights/last.pt` = época 150), agregados por votação -- nunca por um
  checkpoint único (§5.6 do plano). B2 e não A_joint: B2 foi treinado só
  com dados reais e nunca viu uma colagem, então seu "acerto" mede
  realismo/plausibilidade da composição sem circularidade. A_joint,
  treinado nesse mesmo estilo de colagem, acertaria por familiaridade com
  o estilo, não por qualidade -- risco de circularidade já registrado.
- **Entregue**: `scripts/inferir_colagens_sondagem.py` -- a ÚNICA etapa
  de GPU do Estágio A. Roda os 3 checkpoints sobre as 6.640 imagens de
  sondagem com limiar de confiança mínimo (0,001), salvando TODAS as
  detecções brutas (caixa + confiança) num CSV por checkpoint no Drive,
  mais um `metadata_inferencia.json` registrando a configuração exata.
  Desenho deliberado para gastar GPU uma única vez: qualquer decisão
  posterior (limiar, IoU, votação) é feita em CPU sobre os dados salvos.
- **Custo estimado de GPU**: ~20 mil inferências de YOLO11n em 640px --
  poucos minutos no total. É a etapa mais barata em GPU de todo o
  projeto até aqui.
- Suíte completa: 93/93 (script de execução real, sem teste unitário --
  mesmo padrão dos demais scripts dependentes de GPU).
- **Ação pendente para você rodar no Colab**: executar o script -- ainda
  não fiz isso, não tenho acesso ao Drive nem à GPU.

## 2026-09-14 — Inferência concluída e sanidade confirmada; módulo de construção do alvo entregue

- **Inferência (única etapa de GPU do Estágio A) concluída**: 3
  checkpoints de B2 sobre 6.640 imagens de sondagem, ~330s cada (~17 min
  no total). 219.021 / 202.090 / 210.199 detecções brutas (conf >= 0,001)
  para seeds 42 / 123 / 2024.
- **Sanidade confirmada antes de construir o alvo** (decisão de não
  seguir cegamente): em conf >= 0,25, média de **~4,06 detecções por
  cena** nos três checkpoints -- coincide com os ~3,8 objetos colados por
  cena conhecidos (1.267 caixas / 332 imagens de val). ~97% das cenas com
  ao menos uma detecção. Três seeds altamente consistentes entre si
  (26.067 / 25.993 / 26.443 detecções em 0,25). Nenhum sinal de alvo
  degenerado; vale seguir.
- **Entregue**: `src/attribution/alvo.py` -- `construir_alvo()` casa cada
  caixa colada (manifesto) com as detecções da mesma cena via IoU
  (reaproveita `_calcular_iou` já testada), registrando por seed a MAIOR
  confiança casada (score contínuo) e o acerto binário no limiar; agrega
  entre seeds por votação majoritária (`acerto_votacao`) e por média de
  confiança (`conf_media`), as duas formas previstas em §5.6. Preserva
  todas as colunas do manifesto (as features do Estágio A). Limiar e IoU
  são parâmetros -- decisões reversíveis em CPU.
- `scripts/construir_alvo_estagio_a.py` roda contra os dados reais do
  Drive (padrão: iou_min=0,5, conf_min=0,25) e salva a tabela de alvo +
  resumo das taxas de acerto.
- Coberto por `tests/test_alvo.py` (7 testes: IoU alto/conf alta,
  detecção longe, IoU alto/conf baixa, votação majoritária, votação
  minoritária, isolamento por cena, preservação de colunas). Suíte
  completa: **100/100**.
- **Ação pendente para você rodar no Colab (CPU)**: executar
  `construir_alvo_estagio_a.py` e reportar as taxas de acerto -- é o
  número que decide se o alvo está balanceado o bastante para o GBM
  (§5.4 do plano prevê o cenário de desbalanceamento e a alternativa
  por aprendizagem em grupos, se necessário).

## 2026-09-14 — Alvo binário do Estágio A construído: 70,2% de acerto por votação

- **Resultado** (iou_min=0,5, conf_min=0,25, 25.340 caixas coladas):
  taxa de acerto por seed 0,692 / 0,693 / 0,704; **por votação
  majoritária: 0,702**. Alvo na faixa intermediária-alta -- informativo,
  não degenerado. Desbalanceamento 70/30 leve, tratável (AUC-PR como
  métrica do modelo substituto, §5.4).
- **Consistência interna registrada (não conclusão causal)**: a taxa de
  acerto sobre objetos COLADOS (~0,70) coincide com o recall do B2 sobre
  objetos REAIS de validação (~0,69, Fase 1). O detector treinado só com
  real reconhece composições com praticamente a mesma frequência que
  reconhece o real -- coerente com a sanidade anterior (~4 detecções por
  cena vs. ~3,8 objetos colados). Sugere plausibilidade visual média das
  composições, sem afirmar nada sobre quais características a explicam
  (isso é o que o GBM+SHAP vai testar).
- **Decisão: seguir para a tabela de features.** Alvo salvo em
  `estagio_a/alvo/alvo_iou0.5_conf0.25.csv` no Drive, com o score
  contínuo (`conf_media`) preservado para eventual reanálise com outro
  limiar sem refazer inferência.

## 2026-09-14 — Tabela de features de CPU do Estágio A (Famílias 1, 2, 3)

- **`src/attribution/features.py` mantido** (já existia, sem testes):
  após leitura integral, avaliado como superior ao que seria escrito de
  novo em três pontos -- `cobertura_mascara` recalculada direto do alpha
  do PNG (sem join frágil por nome de arquivo com os manifestos de
  extração); Laplaciano restrito a pixels cujos 4 vizinhos estão dentro
  da máscara (elimina a "aresta falsa" transparente/opaco de forma mais
  completa que descartar só a margem externa); `distorcao_aspect` com
  sinal (preserva a direção da deformação). Nenhuma sobrescrita.
- **Decisão registrada -- `pct_escala_alvo` omitida deliberadamente**:
  como as caixas coladas são as próprias caixas reais do alvo, o percentil
  da área dentro do perfil do alvo é uma transformação monotônica de
  `area_caixa_norm`. Árvores de decisão (o GBM) são invariantes a
  transformações monotônicas de uma feature -- seria a mesma informação
  com outro nome. Não adiciona nada ao modelo substituto.
- **Entregue**: `tests/test_features.py` (14 testes para o módulo
  existente, incluindo `test_fundo_transparente_nao_contamina_medidas`,
  que prova numericamente que o fundo transparente NÃO entra no
  contraste nem na nitidez); `src/attribution/tabela.py`
  (`construir_tabela_features`, com cache de intrínsecas por crop único --
  as 25.340 colagens reutilizam crops do pool com reposição; e
  `construir_indice_crops`, que localiza crops por nome-base já que o
  caminho registrado no manifesto é o local da sessão de composição, que
  não existe mais); `tests/test_tabela.py` (4 testes, incluindo prova de
  que `coerencia_escala_pos` é idêntica dentro do mesmo grupo geométrico,
  §5.1); `scripts/construir_tabela_features.py`.
- **Regressão de coerência ajustada nas caixas reais do split de
  VALIDAÇÃO** (o mesmo sobre o qual as colagens foram feitas), não do
  treino -- coerente com a origem das caixas coladas.
- Suíte completa: **118/118**.
- **Ação pendente para você rodar no Colab (CPU)**: executar o script --
  ainda não fiz isso. Além dos números de resumo, vou querer os
  coeficientes da regressão de coerência (esperado: b > 0, "objetos mais
  baixos no quadro tendem a ser maiores", relação de perspectiva) como
  checagem de sanidade antes de treinar o GBM.

## 2026-09-14 — Tabela de features construída: coerencia_escala_pos degenerada neste domínio

- **Tabela construída**: 25.340 linhas × 48 colunas, 21.937 crops únicos
  referenciados, 0 crops não localizados, nenhum NaN nas intrínsecas.
- **Regressão de coerência**: a=-6,971, b=0,038 (1.267 caixas reais de
  val). `b` positivo (direção esperada) mas desprezível: ao longo de todo o
  quadro, a área esperada muda por fator de apenas e^0,038 ≈ 1,04.
- **Causa de domínio, verificada**: `pos_v` das caixas reais concentrado
  na linha do horizonte (mediana 0,53, quartis 0,49-0,60, desvio 0,13) --
  câmera de vigilância costeira, sem gradiente vertical de perspectiva.
  Não é defeito de cálculo; é a estrutura real do CITRA-3D-Real.
- **Consequência**: correlação(`coerencia_escala_pos`, log área) =
  **1,0000**. Sem gradiente, o resíduo é log(área) - constante --
  transformação monotônica de `area_caixa_norm`, invisível para o GBM.
  **Feature removida do conjunto do modelo** (redundância exata, mesmo
  argumento já aplicado a `pct_escala_alvo`).
- **Impacto sobre a previsão pré-registrada P1**: seu terceiro elemento
  (coerência espacial) NÃO é testável como feature independente neste
  domínio -- não por a hipótese estar errada, mas porque o alvo não tem a
  estrutura de perspectiva que a feature pressupõe. Registrado como
  achado, não como refutação. Expectativa concreta derivada para P7: no
  UA-DETRAC (câmera de trânsito, perspectiva forte), `coerencia_escala_pos`
  deve ter variância real e ser testável -- a hipótese de coerência
  espacial fica adiada para o segundo domínio.
- **Multicolinearidade preliminar (§5.5)**: único par acima de |r|=0,7
  entre features retidas é `area_caixa_norm` × `menor_lado_caixa_px`
  (r=0,82, duas medidas do tamanho da mesma caixa) -- tratado como um
  cluster "tamanho_caixa" na leitura do SHAP. `log_fator_reescala` não é
  colinear com nenhuma outra acima de 0,7: carrega informação própria.
- **Taxa de acerto por fonte (univariada, sem controle -- registrada, não
  interpretada)**: ABOShips 0,675, SMD 0,713, SeaShips 0,721,
  InaTechShips 0,734. O GBM/SHAP é que dirá o que explica a diferença.
- **Decisão: seguir para o GBM** com o conjunto de features retidas,
  validação cruzada por grupo (`grupo_geometrico_id`), AUC-PR como métrica
  do portão.

## 2026-09-14 — Modelo substituto (GBM) com validação por grupo e portão pré-registrado

- **Decisões fechadas ANTES de qualquer resultado** (confirmadas pelo
  usuário): (1) 13 features de entrada (após remoção de
  `coerencia_escala_pos`), `fonte` fora do modelo principal -- entra só
  num segundo modelo para o teste de mediação de P3; (2) alvo =
  `acerto_votacao`; (3) validação cruzada por GroupKFold sobre
  `grupo_geometrico_id`, 5 folds; (4) **piso do portão: AUC-PR média
  >= 0,78** (taxa base 0,702; exige ganho de ~8 pontos sobre o acaso).
  Registrado como constante `PISO_AUC_PR` no código -- não ajustável
  depois de ver o resultado.
- **Entregue**: `src/attribution/modelo.py` -- `HistGradientBoostingClassifier`
  com hiperparâmetros fixos e modestos (max_depth=4, min_samples_leaf=50,
  regularização L2), deliberadamente conservador: o objetivo é um
  substituto interpretável, não um classificador ótimo; hiperparâmetros
  pequenos reduzem o risco de o SHAP refletir sobreajuste em vez de
  estrutura.
- **Teste de contraste incluído** (`test_alvo_aleatorio_nao_passa_o_portao`):
  com alvo sem relação com as features, a AUC-PR fica perto da taxa base
  e o portão REJEITA -- prova que o portão discrimina sinal de ruído, não
  passa qualquer coisa.
- **Lição registrada ao escrever o teste**: AUC-PR depende fortemente da
  taxa base. Uma primeira versão do dado sintético tinha base 0,38 e o
  piso absoluto 0,78 (calibrado para base 0,70) rejeitava um sinal
  genuinamente forte. Corrigido calibrando o dado sintético para base
  ~0,69, como o real. Confirma que o piso de 0,78 só faz sentido para a
  taxa base real de 0,70 -- se a taxa base mudar (ex.: outro limiar de
  confiança no alvo), o piso precisa ser re-derivado, não copiado.
- Coberto por `tests/test_modelo.py` (6 testes, incluindo verificação de
  que nenhum grupo aparece em mais de um fold de teste). Suíte completa:
  **124/124**. `scikit-learn` e `pandas` adicionados ao requirements.
- **Ação pendente para você rodar no Colab (CPU)**:
  `scripts/validar_modelo_estagio_a.py`. Se o portão NÃO passar, o plano
  (§9, Fase 2) manda revisar o alvo -- não forçar SHAP sobre um modelo
  sem poder preditivo.

## 2026-09-14 — Portão do modelo substituto PASSOU: AUC-PR 0,857 (piso 0,78)

- **Resultado** (25.340 linhas, 1.267 grupos, 5 folds por grupo):
  AUC-PR por fold [0,850, 0,861, 0,871, 0,832, 0,870], média **0,8569**
  (desvio 0,016), ganho de **+15,5 pontos** sobre a taxa base 0,702.
  AUC-ROC média 0,7526.
- **Portão pré-registrado (>= 0,78) passou com folga**, e de forma
  consistente entre folds -- não é um fold sortudo.
- **Leitura calibrada**: AUC-PR é inflada pela taxa base alta (70% de
  positivos); o AUC-ROC de 0,75 (independente da base) indica
  discriminação real mas moderada. Adequado para um substituto
  interpretável -- sinal suficiente para o SHAP ler estrutura, sem
  desempenho tão alto que sugerisse vazamento.
- **Decisão: seguir para o SHAP** (ranking, direções, estabilidade por
  bootstrap POR GRUPO, clusters de features colineares). CLIP (GPU) só
  depois de ver o ranking, conforme combinado.
- **Lembrete operacional** (já registrado em 2026-09-01): `shap` exige
  numpy>=2 e `sam3` exige numpy<2 -- o SHAP deve rodar numa sessão do
  Colab SEM o `sam3` instalado.

## 2026-09-14 — Análise SHAP: ranking, clusters e estabilidade por bootstrap por grupo

- **Entregue**: `src/attribution/shap_analise.py` -- (1) ranking por
  |SHAP| médio com DIREÇÃO do efeito (correlação valor-da-feature ×
  valor-SHAP); (2) agregação por cluster de features colineares (§5.5):
  `tamanho_caixa` = {area_caixa_norm, menor_lado_caixa_px}, r=0,82, para
  que duas medidas da mesma coisa não dividam entre si um sinal que,
  somado, seria o dominante; (3) estabilidade por bootstrap reamostrando
  GRUPOS geométricos com reposição (nunca linhas -- as 20 variações de
  uma caixa não são independentes), retreinando e recalculando o
  ranking a cada reamostra.
- `shap.TreeExplainer` confirmado compatível com
  `HistGradientBoostingClassifier` no ambiente antes de escrever o
  módulo (shap 0.52, sklearn 1.8, numpy 2.4).
- **Teste de recuperação de sinal plantado** (`test_feature_com_sinal_plantado_fica_em_primeiro`):
  dado sintético com sinal em `log_fator_reescala` -> o SHAP a recupera
  em 1º lugar, com importância > 2× a da 2ª, e ela permanece no top-3 em
  >= 90% das reamostras de bootstrap. Prova que o pipeline SHAP recupera
  estrutura conhecida antes de ser aplicado a dado real.
- Coberto por `tests/test_shap_analise.py` (6 testes, incluindo prova de
  que a reamostragem é por grupo, não por linha). Suíte completa:
  **130/130**. `shap` adicionado ao requirements.
- **Ação pendente para você rodar no Colab (CPU, sessão SEM sam3)**:
  `scripts/analisar_shap_estagio_a.py`. O resultado é o que confronta as
  previsões P1-P4 pré-registradas -- ler contra
  `docs/pre_registro/previsoes_fase0.md`, não contra a intuição do
  momento.

## 2026-09-14 — SHAP do Estágio A: P1 refutada pelo critério pré-registrado; geometria domina o alvo

- **Ranking estável (30 reamostras por grupo)**: top-4 é inteiramente
  Família 3 -- `area_caixa_norm` (pos. 1,13; 100% top-5),
  `menor_lado_caixa_px` (1,97; 100%), `aspect_caixa` (3,73; 97%),
  `pos_v` (3,33; 97%). Cluster `tamanho_caixa` = 0,928 de importância,
  quase 4× o 2º colocado. `log_fator_reescala`: posição 9,4 ± 1,0, **0%
  no top-5**.
- **P1 (pré-registrada) REFUTADA para o Estágio A** pelo seu próprio
  critério ("cair fora do top 8"): `fator_reescala` está fora do top 8 de
  forma estável. Registrado sem suavização -- é para isso que o
  pré-registro existe. (O 2º elemento de P1, `novidade_pool`, ainda não é
  testável -- exige CLIP; o 3º, `coerencia_escala_pos`, já registrado
  como degenerado neste domínio.)
- **P4** (volume do pool não é preditor): não há feature de volume no
  modelo -- satisfeita por construção nesta rodada, NÃO como confirmação
  empírica. Registrado com honestidade.
- **Achado metodológico central**: decomposição da variância do alvo --
  **57,8% entre grupos** (geometria herdada da caixa real, idêntica entre
  as 20 variações) vs. **42,2% dentro do grupo** (só pode vir do
  crop/composição). 65,7% dos grupos são "intermediários" (qual crop é
  colado muda o resultado); 24,3% sempre detectados e 10,0% nunca
  (determinados pela geometria, independente do crop). O SHAP sobre o
  alvo total está dominado pelos 58% geométricos, que abafam o sinal de
  composição -- mas esse sinal existe (42%) e as features de crop mostram
  direções coerentes e estáveis: `contraste` +0,92, `brilho_medio`
  -0,88, `distorcao_aspect` -0,77, `log_fator_reescala` -0,48,
  `crop_menor_lado_original_px` +0,56.
- **`upsample` removida**: importância exatamente 0,0 -- é função
  determinística do sinal de `log_fator_reescala` (upsample = fator > 1),
  o GBM já tem essa informação. Redundância exata, como
  `coerencia_escala_pos` e `pct_escala_alvo` antes.
- **Decisão (§9, Fase 2: "revisar o alvo do modelo"; §5.1 antecipava a
  estrutura)**: análise ADICIONAL com controle de geometria -- incluir
  como feature a taxa de acerto leave-one-out das outras 19 variações do
  mesmo grupo (nunca o rótulo da própria linha, para não vazar o alvo),
  remover as features geométricas puras (absorvidas pela taxa do grupo),
  e rodar GBM+SHAP+bootstrap sobre as features de CROP. Reportada
  separadamente da P1 -- responde outra pergunta: dado que a caixa tem
  detectabilidade própria, quais propriedades do crop deslocam o
  resultado? NÃO é resgate de P1.
- **Nota operacional**: o ambiente de trabalho local do assistente foi
  reiniciado nesta data; repositório reclonado do GitHub (commit 25fe995)
  sem perda -- confirma o valor de manter tudo commitado.

## 2026-09-14 — Análise controlada por grupo: o efeito de escala é real, não-monotônico e assimétrico

- **Entregue**: `src/attribution/controle_grupo.py` -- `adicionar_taxa_grupo_loo()`
  (taxa de acerto das OUTRAS variações do mesmo grupo, leave-one-out) e
  `features_controladas()` (covariável de grupo + 7 features de crop; sem
  geometria pura, sem `upsample`). `tests/test_controle_grupo.py` (5
  testes) inclui **prova por contraste de não-vazamento**: numa linha que
  é a única diferente do seu grupo, a covariável aponta na direção OPOSTA
  ao rótulo dela (anticorrelação dentro do grupo) -- só possível se o
  próprio rótulo está excluído. Suíte: 135/135.
- **Validação por grupo do modelo controlado**: AUC-PR 0,9624 (folds
  0,955-0,966, dp 0,004), AUC-ROC 0,9273. Referência com SÓ a covariável
  de grupo: AUC-PR 0,9410, AUC-ROC 0,9050. **Ganho atribuível às
  features de crop: +0,021 AUC-PR, +0,022 AUC-ROC** -- modesto, mas
  consistente entre folds. Implicação honesta: as 7 features de CPU
  capturam só parte dos 42% de variância intra-grupo; boa parte do efeito
  de composição permanece não explicado por elas (candidatos: aparência
  semântica via CLIP, ou ruído irredutível do detector).
- **Ranking SHAP controlado (entre as features de crop), com
  estabilidade em 10 reamostras por grupo**: 1º `contraste` (+0,93; top-4
  em 100%), 2º `crop_menor_lado_original_px` (+0,68; 100%), 3º/4º
  `log_fator_reescala` e `brilho_medio` (50% cada), depois
  `distorcao_aspect` (-0,67), `cobertura_mascara` (-0,54), `nitidez`
  (+0,14, última). Nota: resolução NATIVA do crop importa (2º), a nitidez
  medida por Laplaciano quase não -- a resolução de origem é o que
  carrega a informação, não a textura de alta frequência em si.
- **ACHADO CENTRAL -- dependência parcial de `log_fator_reescala` (SHAP
  médio por faixa)**: curva em U invertido. Pico em log ∈ [-1, +0,5]
  (fator 0,4-1,6, "escala casada"): SHAP +0,18 a +0,19. Cauda de redução
  extrema (log < -3, fator < 0,05): -0,076. Cauda de AMPLIAÇÃO extrema
  (log > +3, fator > 20): **-0,53**. O efeito de escala é real e tem o
  formato que a tese previa -- mas a direção linear (-0,01) era cega a
  ele, porque uma curva com pico no meio tem correlação linear zero por
  construção. A operacionalização pré-registrada (log com sinal, ranking
  linear no modelo total) não conseguia ver o mecanismo.
- **Assimetria não prevista pela tese**: ampliar demais custa ~7× mais
  que reduzir demais (-0,53 vs -0,076). Coerente com a física (reduzir
  alta resolução preserva informação; ampliar crop minúsculo inventa
  borrão) e com o padrão univariado por fonte (ABOShips, crops pequenos
  ampliados, menor taxa; InaTechShips, crops enormes reduzidos, maior).
- **Status frente ao pré-registro -- sem trapaça**: P1 permanece
  REFUTADA como escrita; NÃO será redefinida retroativamente para
  |log_fator|. O efeito não-monotônico é um achado EXPLORATÓRIO do
  Estágio A, que -- pelo desenho em dois estágios -- vira hipótese a
  confirmar causalmente no Estágio B. P5 (escala casada vs. descasada)
  já está pré-registrada e é o teste confirmatório natural. Sugestão de
  refinamento para P5, a decidir ANTES da Fase 3: separar "descasada por
  redução" de "descasada por ampliação", que este resultado indica serem
  condições muito diferentes.
- Resultados salvos: `shap_controlado_estagio_a.json` (validação,
  referência, ranking, dependência parcial, bootstrap).

## 2026-09-14 — P3 (mediação de fonte): não confirmada como escrita; tese subjacente fortemente sustentada por outro caminho

- **Entregue**: `src/attribution/mediacao.py` -- `testar_mediacao_fonte()`
  (fonte em one-hot, importância = soma das 4 colunas; compara modelo
  sem/com mediadoras; critério pré-registrado de queda >= 70% como
  constante `CRITERIO_QUEDA_P3`). `tests/test_mediacao.py` (5 testes),
  incluindo dois cenários de contraste: fonte-como-proxy-de-escala ->
  P3 confirma; fonte-com-efeito-próprio -> P3 não confirma. O teste
  discrimina os dois mundos. Suíte: 140/140.
- **Operacionalização registrada**: `folga_anotacao` (fração de fundo na
  caixa) não existe com esse nome; `cobertura_mascara` é o seu
  complemento (folga ≈ 1 - cobertura) e foi usada como mediadora de folga.
- **Resultado principal (modelo controlado por grupo)**: importância de
  fonte SEM mediadoras 0,0217; COM mediadoras 0,0202; queda 6,7%. Pela
  letra do critério, **P3 NÃO confirmada**. Mas o antecedente de P3
  ("se fonte aparecer com importância alta antes...") NÃO se cumpre
  nessa configuração: fonte já era desprezível (13× menor que contraste)
  -- o teste é vazio nessa forma.
- **Análise por configurações crescentes** (para identificar o caminho
  da mediação): (0) só grupo + fonte: **0,330** (fonte importa quando
  nada de crop é medido -- antecedente cumprido); (1) + só mediadoras de
  P3: 0,138, queda **58,2%** (abaixo dos 70%); (2) + só as OUTRAS 5
  features de crop (contraste, resolução nativa, brilho, distorção,
  nitidez): 0,022, queda **93,4%**; (3) + todas: 0,020, queda **93,9%**.
- **Leitura em três camadas**: (i) P3 como pré-registrada: não
  confirmada -- escala + folga explicam 58%, não >= 70%. (ii) Tese
  subjacente ("fonte não tem efeito próprio; é proxy de propriedades
  mensuráveis"): FORTEMENTE sustentada -- 94% da importância de fonte
  desaparece com as propriedades do crop medidas. (iii) Mecanismo
  diferente do previsto: a mediação passa principalmente por RESOLUÇÃO
  NATIVA do crop e FOTOMETRIA (contraste, brilho), só secundariamente
  por escala/folga. Na config (0), InaTechShips ajuda (+0,97; crops
  enormes) e ABOShips atrapalha (-0,90; 38% dos crops com menor lado
  <20px, Fase 0); SMD/SeaShips ~nulos.
- **Coerência entre análises independentes**: converge com o SHAP
  controlado (contraste e resolução nativa nos dois primeiros lugares em
  100% das reamostras). Os determinantes dominantes de detectabilidade
  no nível do crop são resolução nativa e fotometria; o descasamento de
  escala importa (não-monotonicamente) mas em segundo plano.
- **Implicação para o artigo**: P1 e P3, ambas "não confirmadas" pela
  letra, contam a MESMA história quando lidas com honestidade -- a
  hipótese de escala era direcionalmente certa mas superestimada; a
  hipótese de proxy era certa mas o proxy passa por outras propriedades.
  Isso é o pré-registro funcionando: impede que a narrativa seja ajustada
  ao resultado, e o resultado real é mais interessante que o previsto.
- Resultados salvos: `p3_mediacao_fonte.json`, `p3_mediacao_configuracoes.json`.

## 2026-09-14 — Features CLIP (Família 4): matemática testada em CPU, passada única de GPU preparada

- **Decisão de comparabilidade, verificada no código**: em
  `aplicar_mascara_e_recortar`, `rgba = dstack([recorte_rgb, alpha])` --
  o RGB dos crops salvos é o retângulo original COM fundo; só o alpha
  codifica a máscara. Descartando o alpha, obtém-se o crop retangular
  original, diretamente comparável a um recorte retangular de um objeto
  real (que não tem máscara). Ambos são embutidos assim: like-with-like.
  Consequência registrada: `dist_clip_alvo` mede similaridade de
  aparência do objeto+contexto, não do objeto isolado.
- **Entregue**: `src/attribution/clip_features.py` -- `dist_clip_alvo`
  (1 - cosseno ao centroide normalizado dos objetos reais de val) e
  `novidade_pool` (1 - cosseno ao vizinho mais próximo no pool, EXCLUINDO
  o próprio crop, calculado em blocos porque 86k×86k não cabe em
  memória). `tests/test_clip_features.py` (6 testes): prova que o próprio
  crop é excluído do vizinho (senão todos teriam novidade 0) e que o
  cálculo em blocos é idêntico ao direto. Suíte: 146/146.
- **`scripts/extrair_clip_estagio_a.py`** -- a passada ÚNICA de GPU: CLIP
  ViT-B/32 (`openai/clip-vit-base-patch32` via `transformers`, já
  presente no Colab) sobre TODO o pool (~86 mil crops) e os ~1.267
  objetos reais de val. Pool inteiro, não só os ~22 mil usados: (a) é a
  definição fiel de `novidade_pool`; (b) o resultado serve ao eixo
  "diversidade" do fatorial da Fase 3. Embeddings, índice, features por
  crop (incl. fonte do vizinho mais próximo -- mede redundância entre
  fontes) e metadados salvos no Drive. Feature math em CPU.
- **Ação pendente para você rodar no Colab (GPU)**: o script. Depois,
  tudo é CPU: juntar as duas features à tabela por nome do crop, rerodar
  o modelo controlado + SHAP, e testar P2.
- **Correção (2026-09-14, antes de qualquer GPU gasta)**: versões
  recentes do `transformers` retornam um objeto de saída em
  `get_image_features`, não um tensor. `_tensor_de_features()` extrai o
  tensor em ambas as versões, preferindo `image_embeds` (espaço projetado
  do CLIP, 512-d, o canônico). Testado contra 5 formas de retorno. A
  `dim_embedding` já registrada no metadado revela qual representação
  foi usada (512 = projetado; 768 = pré-projeção).

## 2026-09-14 — Features CLIP extraídas; P2 confirmada (enquadramento original); novidade_pool refutada; CLIP sem ganho preditivo

- **Extração concluída** (CLIP ViT-B/32, 512-d projetado): 85.941 crops
  do pool + 1.267 objetos reais de val. **19 min de GPU** -- a estimativa
  de "poucos minutos" errou por ~4×: a leitura dos 86 mil PNGs em CPU
  dominou, como antecipado como possibilidade. Registrado como erro de
  estimativa.
- **Avisos "channel dimension is ambiguous"**: crops com um lado de
  exatamente 3 px (ambíguo com o nº de canais); o processador assumiu
  canal-primeiro, possivelmente transpondo a imagem. Estão abaixo do
  filtro min_dim_px=20 -- nunca entraram em colagem alguma; afetam no
  máximo o vizinho mais próximo de outros crops minúsculos no pool.
  Sem impacto na tabela de sondagem; GPU não refeita.
- **Fontes são "ilhas" no espaço CLIP**: 99,1% dos crops têm o vizinho
  mais próximo na própria fonte (ABOShips 99,6%, SeaShips 97,7%).
  Consequência direta da decisão like-with-like (retângulo com fundo): o
  CLIP captura contexto de cena. `dist_clip_alvo` tem **64,5% da
  variância entre fontes**; `novidade_pool` 66,9% dentro da fonte.
  InaTechShips é a fonte MAIS distante do CITRA (0,361 vs ABOShips
  0,123) e foi a de MAIOR taxa de detecção -- aparência de domínio aponta
  na direção contrária à detectabilidade. Novidade bate com a natureza
  dos datasets: vídeo (SMD 0,020, SeaShips 0,046) << fotos (InaTechShips
  0,071).
- **Join**: 25.340 linhas, 0 sem feature CLIP.
- **Multicolinearidade (§5.5)**: `dist_clip_alvo` × `log_fator_reescala`
  r=-0,76; × `crop_menor_lado_original_px` r=+0,71; × `novidade_pool`
  +0,69. Pertence ao cluster escala/resolução. Ao entrar no modelo,
  `crop_menor_lado_original_px` caiu de 0,198 para 0,091: importância
  compartilhada, não nova.
- **Ganho preditivo do CLIP no modelo controlado: AUC-PR -0,0003,
  AUC-ROC -0,0003 -- zero.** A variância de composição não explicada
  pelas 7 features de CPU também não é explicada por aparência
  semântica; o resíduo é provavelmente ruído irredutível do detector.
- **P2 (`dist_clip_alvo` fora do top 5)**: no modelo TOTAL (enquadramento
  original do pré-registro), posição **14ª de 14 -- última**:
  **CONFIRMADA**. No modelo controlado (análise adicional), 4,5 ± 1,5 --
  a feature mais instável de todas (assinatura de colinearidade),
  inconclusiva pela letra (dentro do top 5, fora do top 3). Conclusão
  substantiva firme: semelhança de aparência com o domínio-alvo não
  explica detectabilidade de forma independente.
- **P1, 2º elemento (`novidade_pool` no top 3): REFUTADO** -- posição
  9,7 ± 0,5 no controlado (penúltima), 12ª/14 no total, 0% no top-5.
  Com isso, os três elementos de P1 estão resolvidos: fator_reescala
  refutado (com mecanismo não-monotônico real), novidade_pool refutado,
  coerencia_escala_pos degenerado neste domínio.
- **Regra respeitada**: `docs/pre_registro/previsoes_fase0.md` está
  lacrado por hash e NÃO foi editado. O confronto completo vai em
  `docs/resultados_estagio_a.md`, documento separado.

## 2026-09-14 — Fase 3 redesenhada: adendo pré-registrado em rascunho (lacração pendente de decisão de orçamento)

- **Restrição estrutural identificada antes de desenhar**: com geometria
  fixa entre células (obrigatória -- explica 58% da variância), resolução
  nativa e fator de reescala são o MESMO eixo (fator = caixa / nativo).
  "Alta resolução + ampliação" é fisicamente impossível. A emenda
  "adicionar eixo de resolução nativa" colapsa na emenda "refinar escala em
  3 níveis": `reduzida` = alta resolução reduzida; `ampliada` = baixa
  resolução ampliada. Os dois achados do Estágio A eram o mesmo fenômeno.
- **Segundo fator real: contraste do crop** (1º entre as de crop em 100%
  das reamostras; r = +0,35 com tamanho nativo -- separável; todas as
  fontes com massa dos dois lados da mediana, SeaShips a menor com 27%).
- **Desenho**: fatorial completo 3 (escala: casada [0,5-2,0] / reduzida
  < 0,5 / ampliada > 2,0) × 2 (contraste alto/baixo pela mediana do pool
  elegível) = 6 células + controle real-sobreamostrado. Mesmas caixas de
  treino em todas as células; caixas inviáveis em qualquer célula
  excluídas de todas. Nenhuma interação confundida.
- **InaTechShips excluído do fatorial inteiro**: 0,8% `casada`, 0,2%
  `ampliada` -- incompatível com 2 de 3 níveis; manter proporção de fonte
  constante (§5.7) exige as mesmas 3 fontes (SMD, SeaShips, ABOShips, 1/3
  cada) em todas as células. P6 refinada em "efeitos robustos fonte a
  fonte".
- **Previsões novas/refinadas**: P5a (ampliada é o pior nível, > 2,0 pp),
  P5b (casada >= reduzida, direção só), P8 (contraste alto > baixo, > 2,0
  pp), P9 (interação, exploratória), P10 (alguma célula supera o controle?
  -- registrada como questão, não previsão, para impedir leitura post-hoc).
  Árvore de hipóteses e famílias de Holm-Bonferroni declaradas.
- **Entregue**: `docs/pre_registro/adendo_fase3_fatorial.md` (rascunho),
  `scripts/lacrar_adendo.py` (acrescenta ao hashes.json sem tocar nas
  entradas existentes; registra hash cruzado de previsoes_fase0.md;
  RECUSA lacrar com decisão pendente ou re-lacração), `tests/test_lacrar_adendo.py`
  (4 testes). Suíte: 150/150.
- **Decisão pendente (orçamento, do usuário)**: `n_variacoes` ∈ {1, 2, 3}
  -> ~17 / ~33 / ~49 h de GPU. Proposta: 2. O adendo NÃO pode ser lacrado
  até isso ser fixado -- verificado pelo script.
- **Decisão fixada (usuário, 2026-09-14): `n_variacoes = 2`** (~33 h de
  GPU, 2.696 sintéticas por célula). Adendo finalizado, sem marcadores
  pendentes; script de lacração aceita (ensaiado em cópia, hash de
  referência `9fb7a139...`). A lacração REAL é feita pelo usuário no
  repositório, seguida do commit público -- a ordem "lacrar -> commitar"
  é o que constitui a prova.

## 2026-09-14 — Lacração do adendo: commit de conteúdo feito; índice em hashes.json em commit de complemento

- **Commit de lacração do conteúdo**: `efd46997735509be668afcd591863f8df5df8e92`
  (2026-09-14T21:45:34-03:00). SHA-256 do adendo commitado:
  `9fb7a139df119274c62bfee26f23d7ffc91c5e357660ef1276bfc0c503bb58ec` --
  idêntico ao hash de referência do ensaio. **Esta é a prova de
  lacração**: o git endereça o conteúdo por hash, o commit é público e
  datado, e nenhum treino da Fase 3 começou antes dele.
- **O que faltou**: a entrada correspondente em `hashes.json` (passo 2 do
  procedimento). Causa: `scripts/lacrar_adendo.py` e
  `tests/test_lacrar_adendo.py` não estavam no repositório (ficaram só
  num zip de entrega anterior). Não há alteração de conteúdo do adendo.
- **Correção**: script e teste adicionados ao repositório; `hashes.json`
  recebe a entrada do adendo num commit de COMPLEMENTO, que apenas indexa
  o hash já provado pelo commit `efd4699`. Registrado explicitamente para
  que a cronologia fique transparente: conteúdo lacrado em `efd4699`;
  índice acrescentado depois, antes de qualquer treino.

## 2026-09-14 — Robustez do pacote: shap preguiçoso; alinhamento do Python local

- **Fragilidade exposta ao rodar os testes localmente**: `src/attribution/__init__.py`
  importava `shap` de forma antecipada, então construir o alvo ou a
  tabela de features (que não usam SHAP) falhava sem `shap` instalado.
  Corrigido: `import shap` movido para dentro de `calcular_shap()`
  (import tardio). Provado por teste com `shap` bloqueado artificialmente:
  `construir_alvo`, `construir_tabela_features` e `novidade_pool`
  importam e funcionam sem ele.
- Testes que dependem de shap (`test_shap_analise`, `test_mediacao`)
  agora usam `pytest.importorskip("shap")` -- pulam com mensagem clara em
  vez de quebrar a coleta de TODA a suíte.
- `scripts/lacrar_adendo.py`: `Path.is_relative_to` (3.9+) substituído
  por `relative_to` com try/except -- compatível com 3.8.
- **Ambiente local do usuário está em Python 3.8.9** (fim de suporte em
  2024-10; incompatível com as versões de shap/scikit-learn/pandas usadas
  no Colab, Python 3.13). Recomendação registrada: `pyenv local 3.12` +
  venv + `pip install -r requirements.txt`, para que os testes rodem no
  mesmo stack em que o experimento executa. Rodar testes num ambiente
  divergente do de execução esvazia o propósito de rodá-los.

## 2026-09-14 — Fase 3, tarefa 3.2: verificador de viabilidade das células (CPU)

- **Definições verificadas no código antes de escrever** (unidades erradas
  aqui invalidariam o fatorial): `fator_reescala = area_destino /
  area_original` (razão de ÁREAS, compose.py:182) -- consistente com a
  Fase 0 e o adendo; filtro das colagens = min_dim_px=20; conversão
  YOLO->px reutiliza `ler_caixas_yolo` do compositor (mesmo arredondamento).
- **Entregue**: `src/factorial/celulas.py` -- classificação de níveis
  (casada [0,5, 2,0] inclusiva; reduzida < 0,5; ampliada > 2,0; contraste
  alto > mediana, baixo <= mediana), contagem de crops elegíveis por
  (célula, fonte, caixa) via busca binária sobre áreas ordenadas, regra
  "viável em TODAS as 6 células ou excluída de todas", gargalo por célula
  e fonte, e comparação de geometria viáveis vs excluídas (detecta
  exclusão sistemática, ex.: só caixas grandes). `tests/test_celulas.py`
  (9 testes; inclui prova de que a contagem por bisect bate com a
  classificação crop a crop). Suíte: 159/159.
- `scripts/verificar_celulas_fase3.py` (CPU): contraste de TODO o pool
  elegível (cacheado no Drive, uma vez), mediana fixada, viabilidade das
  caixas de treino, e geração de `celulas_fase3.json` (por script, não à
  mão -- adendo §2) + `caixas_viaveis_fase3.csv`.
- **Critério de decisão registrado antes do resultado**: o desenho se
  sustenta se (a) a fração de caixas viáveis for alta o bastante para não
  reduzir drasticamente o volume de treino, E (b) as caixas excluídas
  não diferirem sistematicamente em geometria das mantidas (fração
  "small" comparável). Se (b) falhar, a exclusão muda o perfil de escala
  do conjunto e precisa ser reportada como limitação -- ou o desenho
  revisto por novo adendo.

## 2026-09-15 — Tarefa 3.2 executada: critério (b) FALHOU -- 'ampliada' é fisicamente impossível para caixas small. Treino NÃO iniciado.

- **Resultado da verificação (3×2, adendo efd4699)**: pool elegível
  41.426 crops (SMD 6.679, SeaShips 8.863, ABOShips 25.884); mediana de
  contraste 40,892; 4.489 caixas de treino em 1.348 imagens. Viáveis em
  todas as 6 células: 2.711 (60,4%). Gargalo: `ampliada` (2.766/3.033
  viáveis vs ~4.400 nas demais).
- **Critério (b) falhou**: caixas viáveis têm **0,0% small** (área
  mediana 4.508 px²); excluídas têm **79,7% small** (mediana 624 px²).
  Nenhuma caixa small sobreviveu. O CITRA-3D-Real é 82,2% small (Fase 0):
  o fatorial treinaria composições só em caixas médias/grandes -- o oposto
  do regime dominante do alvo. Suspeita a priori estava errada na
  DIREÇÃO (esperava-se que `reduzida` excluísse as grandes).
- **Mecanismo, quantificado no pool**: o filtro min_dim_px=20 impõe área
  de crop >= 400 px² (pior caso entre fonte×contraste: 680, SMD alto).
  `ampliada` (fator > 2 <=> area_crop < A/2) exige A > 1.360 px² (lado
  > 37 px) -- acima do limiar small (32 px). Impossibilidade FÍSICA do
  desenho, não falta de crops. `casada` exige A >= 340 (lado >= 18 px).
- **Reinterpretação do Estágio A**: a "ampliação extrema" (fator > 20)
  com crops >= 400 px² só ocorreu em caixas > 8.000 px² -- a penalidade
  de -0,53 é um fenômeno de caixas GRANDES. Num alvo small com crops de
  qualidade mínima, os únicos regimes reais são `casada` e `reduzida`.
  Achado metodológico reportável por si.
- **Gargalo de amostragem**: em células viáveis, alguns (célula, fonte)
  têm 1 único crop elegível para alguma caixa (reduzida__baixo SMD=1;
  reduzida__alto SeaShips=1) -- com n_variacoes=2, repetiria o crop.
- **Decisão, conforme a regra pré-registrada**: NÃO treinar. O desenho 3×2
  não se sustenta na população-alvo. Redesenho via NOVO adendo (o
  efd4699 permanece lacrado e é citado como superado, com este motivo).
- **Entregue**: `verificar_viabilidade(..., niveis_escala=...)` e o script
  com `niveis_escala`/`sufixo`, para avaliar o desenho 2×2
  (casada/reduzida × contraste) sobre a população completa em segundos
  (contraste cacheado). Teste adicionado; suíte 160/160.

## 2026-09-15 — Verificação 2×2 sustenta-se; CORREÇÃO de referencial na comparação de geometria (erro do assistente)

- **2×2 (casada/reduzida × contraste), população completa**: min1 -> 4.040
  caixas viáveis (90,0%), 1.313 imagens, gargalos de crop único em
  `reduzida` (SeaShips=1, SMD=1). **min2 -> 3.987 (88,8%), 1.296 imagens,
  sem gargalo abaixo de 3** (pior: casada__alto SMD=3). Custo de min2
  sobre min1: 53 caixas (1,2%). **Adotado min2.** Excluídas: as caixas
  minúsculas (mediana 255 px² nativos ≈ 16 px de lado, abaixo dos 18 px
  que `casada` exige com crops >= 20 px) -- exclusão na cauda inferior.
- **ERRO CORRIGIDO (do assistente)**: `comparar_geometria` aplicava o
  limiar COCO small (32² = 1.024 px²) sobre a ÁREA NATIVA da imagem; o
  perfil da Fase 0 (82,2% small) é no referencial LETTERBOX 640, o que o
  detector vê. Uma caixa de 4.508 px² nativos (mediana das viáveis do
  3×2) tem ~22 px de lado a 640 -- É small no referencial certo. A
  afirmação anterior "nenhuma caixa small sobreviveu ao 3×2" estava
  EXAGERADA por mistura de referenciais. O que o 3×2 excluiu foram as
  caixas abaixo de ~12 px a 640 (~37 px nativos): ~40% do conjunto, as
  menores. A conclusão qualitativa (3×2 corta uma fatia grande e
  sistematicamente pequena do regime do alvo; 2×2 corta só a cauda de
  ~5-6 px a 640) se mantém; os NÚMEROS precisam ser refeitos no
  referencial correto antes do adendo 2.
- Correção: `CaixaAlvo.area_640_px` + `area_letterbox_640()` (mesmo método
  do perfil da Fase 0: fator = 640 / max(W, H)); `comparar_geometria`
  reporta `fracao_small_640` e `lado_mediano_640`, e devolve None (nunca
  um número inventado) se o referencial 640 não estiver disponível.
  Testes: 13 no módulo, incluindo prova de que 4.508 px² nativos em
  1920×1080 conta como small. Suíte: 162/162.
- **Ação**: rerodar o verificador (segundos, contraste cacheado) para o
  3×2 e para o 2×2 min2 com a geometria no referencial correto; só então
  redigir o adendo 2.

## 2026-09-15 — Referencial corrigido: 2×2 min2 preserva o regime do alvo (82,3% small vs 82,2%). Adendo 2 redigido.

- **3×2 (referencial 640)**: viáveis 2.711 (60,4%), lado mediano 22,4 px,
  72,0% small; excluídas lado mediano **8,3 px**, 96,9% small -- exclui
  os 40% menores objetos. Rejeição confirmada no referencial correto (a
  narrativa mudou de "0% small" para "os 40% menores"; a decisão, não).
- **2×2 min2 (referencial 640)**: viáveis **3.987 (88,8%)**, 1.296
  imagens, lado mediano 16,0 px, **82,3% small -- idêntico ao alvo
  (82,2%, Fase 0)**. Excluídas 502: lado mediano 5,3 px (cauda de ~5 px)
  + algumas caixas gigantes sem crop `casada` em alguma fonte. Gargalo
  mínimo 3 (casada__alto, SMD). **Desenho adotado.**
- **Entregue**: `docs/pre_registro/adendo2_fase3_fatorial_2x2.md`
  (supersede a estrutura fatorial do adendo 1; herda o resto; §1
  documenta a rejeição do 3×2 com os números corretos e o erro de
  referencial corrigido). P5b' vira hipótese primária de escala com
  critérios em dois níveis (forte > 2,0 pp; fraca = direção); P5a
  registrada como não testável; P8 mantida; ~23 h de GPU (vs ~33 h).
- **Artefatos copiados para o repositório** (gerados por script, adendo
  §3): `configs/celulas_fase3.json` (2×2 min2, ref. 640) e
  `configs/caixas_viaveis_fase3.csv` (3.987 caixas).
- Script de lacração aceita o adendo 2 (ensaio em cópia); hash de
  referência registrado abaixo. Lacração real: pelo usuário, no
  repositório, seguida do commit público.

## 2026-09-15 — Adendo 2 LACRADO. Início da construção das células (CPU)

- **Commit de lacração**: `a4ec7abdc35a9829f4333d68ceb91b5bf7b7a334`
  (2026-09-14T23:21:38-03:00). SHA-256 do adendo 2:
  `be395b8bbb017ed0f4aac98009934801f32a23625b4dbb653b94da6e215db7e9`,
  idêntico ao ensaio. Adendo 1 (`9fb7a139...`) e artefatos originais
  intactos. `configs/celulas_fase3.json` e `caixas_viaveis_fase3.csv`
  commitados. Nenhum treino iniciado.

## 2026-09-15 — Construção das células (tarefa 3.2, parte 2): seletor injetável no compositor

- **`compor_dataset` estendido** com `seletor_de_crop(imagem_id, caixa, rng)`
  opcional: retorna (fonte, caminho) ou None (= caixa fica REAL, com a
  anotação real mantida no label -- nunca removida, seria falso negativo
  de treino). Sem seletor, comportamento idêntico ao original (os 4
  testes antigos do compositor passam inalterados). Metadata registra
  `n_caixas_mantidas_reais` e `usa_seletor_de_crop`.
- **`src/factorial/seletor.py`**: só as caixas PRÉ-REGISTRADAS
  (`configs/caixas_viaveis_fase3.csv`) recebem colagem, em todas as
  células -- garante "mesmas caixas" mesmo que uma caixa fosse viável
  só em algumas. Entre as permitidas: fonte uniforme entre as 3 (1/3 em
  expectativa), crop uniforme entre os elegíveis (escala pela área da
  caixa, contraste da célula, fronteiras idênticas às da verificação).
  Se uma caixa permitida não tiver `minimo_por_fonte` crops em alguma
  fonte, ERRO explícito (`CaixaPermitidaSemCrop`) -- o pool mudou; não
  silenciar. Determinístico dado o rng do compositor.
- `tests/test_seletor.py` (6 testes): nível de escala e contraste
  respeitados, balanceamento de fonte, erro claro, determinismo, e
  INTEGRAÇÃO com o compositor (caixa não permitida fica real, metadata e
  label corretos). Suíte: **169/169**.
- **`scripts/gerar_celulas_fase3.py`** (CPU): 4 células, seeds fixas
  3101-3104 (registradas), n_variacoes=2, min2. Verifica cada manifesto
  contra o adendo (0 erros de nível de escala e de contraste; proporção
  de fonte; distribuição de fator_reescala) e que o conjunto de caixas
  coladas é IDÊNTICO entre células e igual ao pré-registrado. Zip por
  célula + manifesto + metadata no Drive.

## 2026-09-15 — Células do fatorial 2×2 construídas e verificadas

- **4 células geradas** (seeds 3101-3104, n_variacoes=2): 7.974 colagens
  cada (3.987 caixas × 2), **0 erros de nível de escala e 0 de
  contraste** em todas; conjunto de caixas coladas IDÊNTICO entre
  células e igual ao pré-registrado; proporção de fonte 0,322-0,341.
- **Distribuição de `fator_reescala` (adendo 2 §2)**: `casada` mediana
  0,81-0,85, p05 0,52, p95 1,75-1,82 (dentro de [0,5, 2,0] por
  construção); `reduzida` mediana 0,15-0,19, p05 **0,014-0,021** (crop
  50-70× a área da caixa), p95 0,45-0,46. `reduzida` agrupa reduções
  moderadas e extremas -- heterogeneidade registrada; análise secundária
  pré-registrada (F3) olha a distribuição.
- **Justificativa do override `permitir_split_treino=True`** (o
  compositor exige registro): as células são DADOS DE TREINO -- compor
  sobre o split de treino é o desenho correto. A proibição existe para
  as colagens de SONDAGEM do Estágio A (memorização de cena pelo detector
  rotulador), que não se aplica aqui.
- Artefatos no Drive: `fase3/celulas/{célula}.zip` (imagens+labels),
  `manifesto_{célula}.csv`, `metadata_{célula}.json`, `resumo_celulas_fase3.json`.

## 2026-09-15 — Fase 3: preparação de dados e executor de treino retomável

- **`src/train/executar.py`** -- executor reaproveitável (Fase 3 e 4):
  `execucao_concluida()` exige `results.csv` com exatamente
  `epochs_total` linhas, última época igual a `epochs_total`, E
  `weights/last.pt` (a checagem rigorosa da Fase 1, agora em código);
  `execucoes_pendentes()`; `copiar_resultados_para_drive()` ao final de
  CADA execução; `treinar_execucao()` com o protocolo V2. `tests/test_executar.py`
  (7 testes: parcial, sem last.pt, época final errada, pasta inexistente
  -> não concluída). Suíte: **176/176**.
- **`scripts/preparar_dados_locais_fase3.py`** (CPU): real train/val
  locais, extração das 4 células, trainlists (célula = real × 2 +
  sintéticas da célula, ~51/49; controle = real × 2), data.yaml por
  braço, e **`contagens.json`** com imagens/época por braço -- lido pelo
  treino, nunca codificado à mão (lição do `N_IMAGENS_EPOCA` do piloto).
- **`scripts/treinar_fase3.py`** (GPU): 15 execuções planejadas (4
  células + controle) × seeds 42/123/2024, em ORDEM FIXA seed-externa /
  braço-interno -- a cada 5 execuções, todos os braços têm a mesma seed
  completa (uma réplica inteira analisável mesmo se o orçamento parar no
  meio). `main()` roda só as pendentes; `listar()` mostra o estado;
  `max_execucoes` permite dosar por sessão. Cada execução é verificada
  ao terminar (assert) antes de seguir.
- Orçamento: ~1,5 h/execução (5.288 imgs/época nas células, 2.696 no
  controle) -> ~23 h no total, em quantas sessões forem necessárias.

## 2026-09-15 — Desvio pego ANTES do treino: 104 cópias do real por célula, removidas

- A preparação encontrou 2.696 sintéticas por célula, não as 2.592
  pré-registradas (adendo 2 §3.5). Causa: 52 imagens de treino sem
  nenhuma caixa viável; o compositor grava a saída mesmo sem colagem
  -> 104 "sintéticas" por célula eram cópias idênticas do real (com o
  label real). Idênticas entre células (sem confound entre elas), mas
  desviavam do pré-registro e criavam uma assimetria pequena contra o
  controle (104 cópias reais extras).
- **Correção**: `remover_sinteticas_sem_colagem()` (src/factorial) apaga
  as saídas de imagens sem colagem, pelo manifesto; a preparação aplica
  por célula, imprime quantas removeu, e ASSERTA que o N sintético é
  igual entre células. Esperado: 2.592 por célula, trainlist 5.288.
  Teste adicionado; suíte 177/177. Nenhuma GPU gasta.
- **Tentativa de treino iniciada sob a preparação com cópias** (antes da
  correção chegar ao Colab): interrompida e DESCARTADA por inteiro --
  `/content/fase3_runs` e `fase3/runs` no Drive apagados, para que o
  executor retomável não considere "concluída" nenhuma execução treinada
  com a trainlist de 5.392. Nenhum resultado dessa tentativa é usado.
  Custo: o tempo de GPU até a interrupção.

## 2026-09-15 — Fase 3, réplica seed 42 completa (5 execuções): leitura provisória, sem vereditos

- **Integridade**: 5 × 150 épocas, curvas sãs, sem anomalias de pipeline.
- **Época 150, recall in-domain (val)**: controle 0,7017; casada__alto
  0,6938; casada__baixo 0,6855; reduzida__baixo 0,6851; reduzida__alto
  0,6796.
- **Contrastes pré-registrados (UMA seed -- o critério exige 3; nenhum
  veredito)**: P5b' casada − reduzida = +0,73 pp (direção prevista,
  abaixo do piso 2,0); P8 alto − baixo = +0,14 pp (~zero); P9 interação
  +1,38 pp (exploratória); P10: todas as células abaixo do controle
  (−0,79 a −2,21 pp).
- **Observações provisórias, a confirmar com 3 seeds**: (1) efeitos na
  faixa do piso de ruído; (2) contraste, a feature de crop mais forte
  para DETECTABILIDADE no Estágio A, não se traduz em utilidade de
  TREINO -- se confirmado, é a distinção central do projeto ("reconhecer
  o objeto colado" ≠ "aprender com ele"); (3) padrão da Fase 1 repetido:
  células fazem pico mais cedo (épocas 74-103 vs 121 do controle) e caem
  mais até a 150 (2,6-3,5 pp vs 1,4); no pico, casada__baixo (0,720)
  supera o pico do controle (0,716). A época fixa 150 captura o
  sobreajuste mais rápido dos braços com sintético -- fenômeno medido,
  não escondido (decisão da Fase 1); comparação no pico é EXPLORATÓRIA
  (F3), nunca primária.
- **Decisão: continuar sem alteração** (seeds 123 e 2024). Não há
  problema de pipeline; efeitos pequenos são resultado, não defeito; P8
  nulo e P10 negativo só são críveis com 3 seeds.
- **Análise secundária pré-registrada pendente** (recall estratificado
  por tamanho): exige uma passada de inferência dos 15 `last.pt` sobre
  val (332 imagens × 15 modelos -- trivial), após as 3 seeds.

## 2026-09-16 — Fase 3 completa: 15 execuções íntegras; análise fatorial; vereditos

- **Entregue**: `src/factorial/analise.py` -- ANOVA 2×2 com seed como
  bloco, contrastes pré-registrados por seed (t pareado, d de Cohen,
  leave-one-seed-out), regra do piso (real / direção / ruído), Holm por
  família. Distribuições t e F implementadas sem scipy e validadas contra
  valores tabelados (`tests/test_analise.py`, 10 testes). Suíte 187/187.
- **Resultados (época 150, recall val)**: controle 0,7051; casada__baixo
  0,6926; casada__alto 0,6896; reduzida__baixo 0,6834; reduzida__alto
  0,6829. ANOVA: escala p=0,056; contraste p=0,62; interação p=0,72;
  **seed p=0,008**.
- **Vereditos pela letra (adendo 2)**: P5b' **confirmação fraca** (+0,80
  pp, direção nas 3 seeds, abaixo do piso); P8 **refutada** (−0,18 pp,
  nulo); P9 ruído; P10: **nenhuma célula supera o controle**, 12/12
  pares negativos, média −1,80 pp (d=−6,95, p=0,007), reduzida__* passam
  o critério "real" (−2,2 pp). P5 original refutada (abaixo do piso); P6
  original não aplicável (resolvida por desenho).
- **P6' NÃO TESTÁVEL -- erro de desenho do adendo 2**: exige treinos com
  sintético restrito a cada fonte (36 execuções), não orçados. Registrado
  como falha do adendo, não como resultado. Lição: cada previsão deve
  vir com a lista explícita das execuções que a testam.
- **F3 (exploratório, no pico)**: células e controle EMPATAM no pico
  (−0,15 a −0,57 pp, sinais mistos); células fazem pico 20-45 épocas
  antes e caem 2-3× mais até a 150. A composição não abaixa o teto --
  acelera o sobreajuste. A época fixa (Fase 1) expôs isso; seleção por
  validação o teria escondido.
- **Achado central sobre o método**: contraste -- feature de crop mais
  forte para DETECTABILIDADE no Estágio A -- tem efeito NULO como fator
  de TREINO. O alvo-proxy do Estágio A mede plausibilidade, não
  utilidade. Atribuição observacional sobre proxy de detectabilidade não
  substitui manipulação causal; o desenho em dois estágios foi o que
  permitiu ver a divergência.
- `docs/resultados_fase3.md`: confronto pela letra, leitura substantiva
  separada, limitações. `scripts/recall_por_tamanho_fase3.py`: F2
  pendente (inferência dos 15 last.pt sobre val; definição fixada antes
  do resultado: conf>=0,25, IoU>=0,5, casamento guloso, estrato a 640).

## 2026-09-16 — F2 (recall por tamanho) concluída: composição ≈ neutra nos small, prejudicial nos não-small

- val: 1.086 small (85,7%), 181 não-small. **Caveat**: o piso de 2,0 pp
  não está calibrado para 181 caixas (1 caixa = 0,55 pp; flutuação
  binomial ~2,5 pp por execução) -- vereditos "real" no estrato não-small
  não são confiáveis pelo critério pré-registrado.
- Small: células − controle −0,70 pp (dentro do ruído); contraste +0,57
  pp (3/3 seeds); escala +0,32 (mista). Não-small: −2,44 pp; contraste
  +1,01 (3/3); escala −0,64 (mista).
- Refina, não inverte: o prejuízo agregado vem dos não-small; no regime
  dominante do alvo a composição é ≈ neutra. Contraste: direção positiva
  consistente a limiar fixo, mas < 1 pp e de sinal oposto na métrica
  primária (limiar de máximo-F1) -- nulo a minúsculo. P8 permanece
  refutada. Nenhum estrato com célula acima do controle.
- **Fase 3 fechada.** `docs/resultados_fase3.md` atualizado.

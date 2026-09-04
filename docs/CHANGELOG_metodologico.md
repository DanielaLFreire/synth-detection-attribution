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

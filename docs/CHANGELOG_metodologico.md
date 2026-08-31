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

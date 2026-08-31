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

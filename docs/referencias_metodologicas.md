# Referências metodológicas

Banco de referências científicas citadas para justificar decisões de método
neste projeto. Cada entrada indica **onde** a referência foi usada, para
facilitar a redação da seção de métodos do artigo. Atualizar sempre que uma
nova decisão for justificada por literatura.

---

### Reprodutibilidade e organização de projeto

- **Sandve, G.K., Nekrutenko, A., Taylor, J., Hovig, E. (2013).** "Ten Simple
  Rules for Reproducible Computational Research." *PLoS Computational
  Biology*, 9(10): e1003285.
  Uso neste projeto: fundamenta a estrutura do repositório (§ estrutura geral
  do repositório, controle de versão, registro de proveniência de cada
  resultado).

- **Wilson, G., Bryan, J., Cranston, K., Kitzes, J., Nederbragt, L., Teal,
  T.K. (2017).** "Good enough practices in scientific computing." *PLoS
  Computational Biology*, 13(6): e1005510.
  Uso neste projeto: fundamenta a separação entre código versionado (Git) e
  dados/artefatos pesados (armazenamento externo documentado).

- **Wilkinson, M.D. et al. (2016).** "The FAIR Guiding Principles for
  scientific data management and stewardship." *Scientific Data*, 3, 160018.
  Uso neste projeto: fundamenta a convenção de organização de dados no Drive
  (manifesto com hash ao lado de cada artefato pesado, §12.1 do plano).

### Interpretabilidade e atribuição causal (a preencher conforme o Estágio A/B avançar)

- *(pendente)* Referência sobre SHAP e o cuidado com features correlacionadas
  — a citar quando implementarmos §5.5 do plano (tratamento de
  multicolinearidade).
- *(pendente)* Referência sobre desenho fatorial fracionado e resolução de
  confundimento — a citar quando implementarmos §5.7 (Estágio B).

### Datasets

- **Wen, L. et al. (2020).** "UA-DETRAC: A New Benchmark and Protocol for
  Multi-Object Detection and Tracking." *Computer Vision and Image
  Understanding*, 193.
  Uso neste projeto: segundo dataset-alvo para validação de generalização
  (§2.3 do plano).

- **Teixeira, E.H., Mafra, S.B., De Figueiredo, F.A.P. (2025).**
  "InaTechShips: A validation study of a novel ship dataset through deep
  learning-based classification and detection models for maritime
  applications." *Ocean Engineering*, 326, 120823.
  Uso neste projeto: citação obrigatória da fonte pública InaTechShips,
  usada como uma das quatro fontes de crops (§4 do plano).

### Linhagem intelectual do projeto (não é este projeto, mas é o trabalho do qual ele herda perguntas e lições)

- **Freire, D.L., Teixeira, E.H., Moreira, L.A.S. (2026).** "Visual
  Similarity Is Not Enough: Domain-Adapted Synthetic Data for Maritime
  Vessel Detection." *Engineering Applications of Artificial Intelligence*
  (em revisão). Código: `github.com/DanielaLFreire/maritime-synthetic-detection`.
  Uso neste projeto: origem do achado "similaridade visual não é suficiente"
  que motiva a pergunta de pesquisa deste projeto (§1, §3 do plano — CLIP
  como instrumento de medição, não critério de seleção). Também documenta o
  subconjunto curado/aleatório de 25k imagens do InaTechShips
  (`dataset_25k_v2.zip` no Drive) — **fora do escopo deste projeto**: são
  imagens inteiras para pré-treino direto, experimento já concluído com
  resultado de transferência negativa, categoricamente distinto da
  composição in-place que este projeto investiga. Registrado para não deixar
  dúvida em aberto sobre o conteúdo do arquivo.

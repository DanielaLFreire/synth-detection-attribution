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

- **Hastie, T., Tibshirani, R., Friedman, J. (2009).** *The Elements of
  Statistical Learning: Data Mining, Inference, and Prediction* (2ª ed.).
  Springer. Capítulo 7, "Model Assessment and Selection".
  Uso neste projeto: fundamenta a distinção entre o papel do split de
  validação (seleção de modelo/checkpoint) e do split de teste (estimativa de
  erro de generalização) — usada para justificar por que gerar as colagens de
  sondagem do Estágio A sobre o split de validação (§5.2 do plano) não
  compromete a separação causal observação→confirmação, desde que a seleção
  de checkpoint não dependa do desempenho nesse mesmo split (ver
  `CHANGELOG_metodologico.md`, entrada de 2026-09-01).

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

- **Lin, T.-Y. et al. (2014).** "Microsoft COCO: Common Objects in Context."
  *ECCV 2014*.
  Uso neste projeto: definição de referência para os limiares de tamanho de
  objeto (small < 32² px, medium < 96² px, large ≥ 96² px), adotada no script
  canônico de perfilamento estrutural (tarefa 0.1) para resolver, de forma
  documentada, uma divergência encontrada entre duas medições legadas do
  mesmo indicador no CITRA-3D-Real (ver `CHANGELOG_metodologico.md`,
  entrada de 2026-08-31).

### Composição sintética (copy-paste)

- **Dwibedi, D., Misra, I., Hebert, M. (2017).** "Cut, Paste and Learn:
  Surprisingly Easy Synthesis for Instance Detection." *ICCV 2017*, 1310–1319.
  Uso neste projeto: referência fundacional da técnica de composição
  recorte-e-colagem para detecção de instância — base conceitual do
  componente `src/compose/` (tarefa -1.2).

- **Ghiasi, G., Cui, Y., Srinivas, A., Qian, R., Lin, T.-Y., Cubuk, E.D.,
  Le, Q.V., Zoph, B. (2021).** "Simple Copy-Paste is a Strong Data
  Augmentation Method for Instance Segmentation." *CVPR 2021*, 2918–2928.
  Uso neste projeto: demonstra que colagem posicionada sem modelagem de
  contexto ao redor já produz ganho robusto — justifica a escolha de não
  exigir realismo de contexto na composição in-place deste projeto,
  consistente com a decisão de herdar posições de caixas reais (§5.1).
  Também informa a decisão de que, uma vez isolado o objeto do fundo
  (máscara), técnicas adicionais de blending na borda não são necessárias.

- **Geirhos, R., Jacobsen, J.-H., Michaelis, C., Zemel, R., Brendel, W.,
  Bethge, M., Wichmann, F.A. (2020).** "Shortcut Learning in Deep Neural
  Networks." *Nature Machine Intelligence*, 2(11):665–673.
  Uso neste projeto: fundamenta o risco de que bordas visíveis de colagem
  (recorte retangular com fundo original) sejam aprendidas pelo detector
  como pista trivial de "objeto colado", em vez da aparência real do
  objeto — motiva a adoção de segmentação (SAM) para isolar o objeto do
  fundo antes da colagem (`src/segmentation/`).

- **Kirillov, A. et al. (2023).** "Segment Anything." *ICCV 2023*.
  Uso neste projeto: modelo de segmentação com prompt de caixa
  (`SegmentadorSAM`) usado para isolar o objeto do fundo em cada crop
  antes da composição, mitigando o risco de shortcut learning acima.

- **Carion, N. et al. (2025).** "SAM 3: Segment Anything with Concepts."
  *arXiv:2511.16719*.
  Uso neste projeto: alternativa mais recente ao SAM 1, com desempenho
  declarado superior em objetos finos/pequenos/baixo contraste
  (`SegmentadorSAM3`) — mesmo perfil dos objetos do CITRA-3D-Real.
  Usa prompt de caixa via `Sam3Processor.add_geometric_prompt` (confirmado
  por leitura direta do código-fonte oficial, não documentação de
  terceiros — ver `CHANGELOG_metodologico.md`, 2026-09-01). Acesso aos
  checkpoints pendente de aprovação (Hugging Face); leitura da licença
  registrada na mesma entrada do changelog.

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

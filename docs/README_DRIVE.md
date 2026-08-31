# Convenção de organização — EXPERIMENTO_ATRIBUICAO_CAUSAL

Este documento explica a organização desta subpasta dentro do Drive existente
do projeto (`PROJETO_MARINHA/`). Ele é o equivalente, para dados/artefatos não
versionados, do que o `README.md` e o `docs/CHANGELOG_metodologico.md` são
para o código no GitHub: existe para que qualquer pessoa (inclusive a própria
equipe, meses depois) entenda o que está aqui e por quê, sem depender de
memória de conversa.

Referência completa da decisão e da justificativa: §12.1 do documento
`docs/PLANO_v2_atribuicao_causal_composicao_sintetica.md` no repositório
`synth-detection-attribution` (GitHub).

## Regra central: herdado por referência vs. regenerado

**Reaproveitado por referência (read-only, nunca duplicado, nunca modificado
nesta subpasta)**: datasets-fonte brutos como distribuídos originalmente —
`ABOships.zip`, `seaship.zip`, `SeaShips_voc.zip`, `smd_clean.zip`, imagens
brutas do `InaTechShips`, imagens e anotações originais do `CITRA-3D-Real`.
Esses arquivos continuam vivendo em `PROJETO_MARINHA/Datasets/` — esta
subpasta não os copia, apenas referencia esse caminho na documentação e nos
arquivos de configuração do pipeline.

**Regenerado do zero dentro desta subpasta (nunca reaproveitar os
equivalentes do projeto anterior)**: qualquer crop já segmentado
(`crops_abo.zip`, `InaTechShips_crops_sam.zip` do projeto anterior) e
qualquer `synth_*.zip` antigo. Motivo: esses artefatos foram produzidos sob
filtros de extração inconsistentes entre fontes (MIN_DIM 20px + opacidade vs.
MIN_DIM 50px sem opacidade) e sem o manifesto por colagem que este projeto
exige — reaproveitá-los reintroduziria exatamente os vieses que este projeto
foi desenhado para eliminar.

## Estrutura de pastas

```
EXPERIMENTO_ATRIBUICAO_CAUSAL/
├── README_DRIVE.md                       # este arquivo
├── crops/                                # REGENERADOS sob filtro unificado
│   ├── _manifesto_extracao.json          # hash, parâmetros de filtro, data, fonte
│   ├── crops_abo.zip
│   ├── crops_inatech.zip
│   ├── crops_smd.zip
│   └── crops_seaships.zip
├── labels_final/                         # materializado e versionado (não gerado em runtime)
├── composicao/
│   ├── manifesto_colagens/               # manifesto por colagem — Parquet/CSV em lotes
│   └── synth_*.zip
├── estagio_a/
│   ├── colagens_sondagem_val/            # colagens geradas sobre o split de VALIDAÇÃO
│   ├── features_table.parquet
│   ├── shap_outputs/
│   └── modelos_gbm/
├── estagio_b/
│   ├── runs/                             # por célula do fatorial, por seed
│   └── results_fatorial.csv
├── segundo_dominio_uadetrac/             # validação de generalização (UA-DETRAC)
│   ├── fonte_ref.md                      # origem, hash, licença do UA-DETRAC
│   ├── crops_veiculos/
│   └── estagio_a_uadetrac/
└── pre_registro/
    ├── commit_fase0.md                   # previsões lacradas
    └── hashes.json                       # hash de cada artefato citado no pré-registro
```

## Convenções de armazenamento (herdadas por serem boas práticas verificadas)

- **Um `.zip` por artefato pesado**, não pastas soltas com muitos arquivos
  pequenos — evita escrita arquivo-a-arquivo lenta e vulnerável a queda de
  conexão quando o Drive é montado via FUSE (lição já documentada no projeto
  anterior).
- **Nenhum artefato gerado é considerado válido para análise sem seu
  manifesto correspondente presente ao lado dele** (hash, parâmetros, data).
  Um `.zip` sem manifesto é tratado como não confiável e não deve ser citado
  em nenhuma tabela do artigo.
- Pastas ainda vazias nesta estrutura são propositais — marcam onde cada fase
  do plano vai escrever; não apagar por parecerem "vazias sem motivo".

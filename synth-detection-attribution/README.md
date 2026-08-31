# Causal Feature Attribution for Synthetic Data Composition in Small-Object Detection

Independent research project on **causal attribution** of crop-, source-, and
composition-level characteristics that determine the quality of synthetically
composed training data for small-object detection, using in-place synthetic
compositing (segment-and-paste) as the composition method under study.

This project is **not** a continuation of a prior conference-stage codebase
(`maritime-crossdomain`); it reuses methodological lessons from that prior work
(cited where relevant) but has its own baseline, its own pipeline, and its own
pre-registration. See `docs/PLANO_v2_atribuicao_causal_composicao_sintetica.md`
for the full pre-registered experimental plan (in Portuguese, the working
language of the research team).

## Research question

> Given an operational target dataset with a measured structural profile,
> which characteristics of the crops, of the source datasets, and of the
> compositing process **causally determine** the quality of a synthetic
> dataset assembled from public sources for small-object detection on the
> target — and which plausible characteristics do **not**?

The design separates cheap observational **discovery** (gradient boosting +
SHAP over per-paste features) from expensive controlled **confirmation**
(factorial manipulation of the top candidate features), because observational
feature importance is not, by itself, evidence of causality.

## Status

Pre-registration in progress (Phase 0 of the plan in `docs/`). No GPU training
has started. See `docs/CHANGELOG_metodologico.md` for the running log of
methodological decisions.

## Repository structure

```
.
├── configs/        # dataset paths and pipeline parameters (edit here, not in code)
├── src/
│   ├── compose/       # in-place synthetic compositing WITH a per-paste manifest
│   ├── profiling/      # structural profiling of target and source datasets
│   ├── attribution/    # Stage A: feature table, gradient boosting, SHAP
│   ├── factorial/       # Stage B: factorial cell design, ANOVA
│   └── train/          # frozen training protocol
├── scripts/         # numbered pipeline entry points (one per pipeline stage)
├── tests/           # manifest integrity, determinism, and grouping checks
├── results/         # consolidated CSV/Parquet outputs, by phase
└── docs/
    ├── PLANO_v2_atribuicao_causal_composicao_sintetica.md   # pre-registered plan
    ├── referencias_metodologicas.md                          # sources for the methods section
    └── CHANGELOG_metodologico.md                             # methodological decision log
```

Heavy artifacts (raw images, extracted crops, synthetic images, model
checkpoints) are **not** versioned in this repository. They live in a
separate, documented storage location — see `docs/CHANGELOG_metodologico.md`
for the storage convention and what is treated as immutable source data versus
regenerated artifacts.

## Reproducing this work

Setup instructions will be added incrementally as each pipeline stage is
implemented (this repository is being built stage by stage, following the
schedule in `docs/PLANO_v2_atribuicao_causal_composicao_sintetica.md`, §13).
Each stage's script will be documented here once it exists — no step is
described in this README before its code is committed, to avoid the README
promising a pipeline that does not yet run.

## Second validation domain

To assess whether the discovered feature ranking generalizes beyond a single
operational domain, Stage A is additionally replicated on UA-DETRAC (Wen et
al., 2020, fixed-camera traffic surveillance) — chosen to change the content
domain while preserving the structural capture style (fixed camera, small and
distant objects, dense scenes) of the primary target. See §2.3 of the plan for
the full justification and the alternative considered (VisDrone2019-DET).

## Citation

If you use this repository, please cite it as described in `CITATION.cff`.
An accompanying paper is in preparation; this section will be updated with the
full citation once available.

## License

MIT — see `LICENSE`.

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

## Status — experiment closed (2026-09-16)

All four phases are complete and the test split was evaluated exactly once.
Everything below is reproducible from this repository plus the Drive
artifacts listed in `docs/README_DRIVE.md`.

| Phase | What | Where |
|---|---|---|
| 0 | Profiling, coverage, probe compositions, **sealed pre-registration** (P1–P7) | `docs/pre_registro/previsoes_fase0.md`, `hashes.json` |
| 1 | Training pilot: determinism gate, noise floor (2.0 pp), fixed checkpoint (epoch 150) | `docs/CHANGELOG_metodologico.md` (2026-09-09) |
| 2 | Stage A: observational attribution (GBM + SHAP) on a detectability target | `docs/resultados_estagio_a.md` |
| 3 | Stage B: causal 2×2 factorial (scale × contrast), **sealed addendum 2** | `docs/pre_registro/adendo2_fase3_fatorial_2x2.md` (commit `a4ec7ab`), `docs/resultados_fase3.md` |
| 4 | Single evaluation on the untouched test split (guarded) | `docs/resultados_fase4_teste.md`, `fase4/teste_avaliado.json` |

### Main findings (confirmed on the test split)

1. **Segment-and-paste synthetic composition does not beat re-using the
   real data.** Every factorial cell scored below the real-oversampled
   control (−1.75 pp recall, 12/12 paired seed×cell comparisons), and
   ≈ equal to real ×1. Composition accelerates overfitting without
   raising the attainable ceiling.
2. **No manipulated crop characteristic changes that.** Scale matching:
   null on test (a weak, consistent direction on validation did not
   replicate). Crop contrast: null on both.
3. **Detectability proxies do not predict training utility.** Contrast was
   the strongest crop-level predictor of detectability in Stage A and had
   zero effect as a training factor in Stage B. Observational attribution
   over a "does a real-trained detector recognise the paste?" target
   measures plausibility, not usefulness.
4. **A structural limit of the method**: with minimum-quality crops
   (≥ 20 px), "upscaling" is physically impossible for ~82 % of the boxes
   of a small-object maritime target.
5. The pre-registered predictions that failed all failed in the same
   direction (scale and domain similarity over-estimated; native
   resolution and photometry under-estimated) — and they are sealed, so
   the story was not fitted to the result.

Pre-registrations: P1–P7 sealed 2026-09-09 (see `hashes.json`); addendum 1
(`efd4699`, rejected by a pre-declared viability criterion before any
training); addendum 2 (`a4ec7ab`). Test evaluated once at commit `53066ad`.

Total GPU used: ≈ 4.5 h (Phase 1 pilot) + ≈ 0.6 h (Stage A inference +
CLIP) + ≈ 23 h (Phase 3) + minutes (Phase 4).

A follow-up experiment on **real** public images as augmentation (fixed
optimisation steps, image-level scale profile × appearance) is proposed in
the changelog and will live in a separate repository.

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

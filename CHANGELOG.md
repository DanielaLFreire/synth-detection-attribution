# Changelog

All notable changes to this codebase are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- Initial repository skeleton: directory structure, README, LICENSE (MIT),
  CITATION.cff, `.gitignore`.
- Pre-registered experimental plan imported into `docs/`.
- `src/compose/`: in-place synthetic compositing component with per-paste
  manifest (task -1.2). Inherits target bounding boxes (never samples them).
  Refuses to compose over the training split by default (guards against the
  scene-memorization confound, plan §5.2); explicit override required and
  logged. Covered by `tests/test_compose.py` (manifest row count, determinism
  under fixed seed, train-split guard) — all passing.
- `src/extraction/`: unified crop quality filter (task -1.3, partial —
  see docs/CHANGELOG_metodologico.md for exact scope). Roboflow-augmentation
  deduplication (`dedup_roboflow.py`), source-agnostic quality filter with
  configurable thresholds (`quality_filter.py` — no hardcoded threshold
  values, deliberately, to avoid repeating the ABOShips-vs-InaTechShips
  filter-inconsistency confound documented from the prior project), and a
  hashed extraction manifest (`quality_manifest.py`) producing the exact
  `pool_crops` format expected by `src.compose.compor_dataset`. Covered by
  `tests/test_extraction.py` (12 tests) — all passing. NOT yet implemented:
  per-source native annotation readers (ABOShips CSV, SMD format) — deferred
  to task -1.6, pending direct inspection of those sources' real structure.
- `src/materialize/`: materialização de `labels_final/` com validação de
  integridade e manifesto de hash SHA-256 (task -1.4). Detecta e recusa
  materializar sobre imagem-sem-label, label-sem-imagem, ou linha com classe
  fora do conjunto permitido (reproduz em teste o exato tipo de contaminação
  já encontrado no CITRA-3D-Real — `Quadrado_marcacao(Clone)`). Inclui
  `verificar_labels_final()` para detectar deriva futura via recomputação de
  hash. Scripts de entrada: `scripts/materializar_labels_final.py`,
  `scripts/verificar_labels_final.py`. Covered by `tests/test_materialize.py`
  (7 tests) — all passing. Full suite: 23/23 passing.
- `src/train/protocol.py`: V2 training protocol (task -1.5). Fixes the
  documented warmup-in-epochs bug (a fixed warmup epoch count produces
  different real gradient-step counts across arms with different
  images-per-epoch, e.g. joint synthetic+real vs. baseline) by defining
  warmup in absolute steps and computing the per-arm equivalent fractional
  epoch count. Enforces full-schedule training (`early_stopping_habilitado`
  must be False) and requires an explicit, non-default `epoca_checkpoint`
  (must come from pilot convergence evidence, never copied or assumed).
  Covered by `tests/test_protocol.py` (8 tests, including one that
  reproduces the original bug in miniature and one confirming the fix) —
  all passing. Full suite: 31/31 passing.
- `src/extraction/extrair_crops_yolo.py`: bbox-based crop extraction from
  YOLO annotation (task -1.6, first source: SMD). Captures `video_id` per
  crop (SMD images are video frames — 36 distinct videos — a content-level
  near-duplication axis distinct from but analogous to the Roboflow
  augmentation issue found in SeaShips). Degenerate boxes / orphan labels
  are skipped and logged, not fatal (deliberately less strict than target
  dataset materialization). `scripts/extrair_smd.py` chains extraction +
  unified quality filter (-1.3) + Drive copy. Covered by
  `tests/test_extrair_crops_yolo.py` (6 tests, including real SMD filename
  patterns) — all passing. Full suite: 37/37 passing.
- `src/extraction/extrair_crops_voc.py`: bbox-based crop extraction from
  VOC XML annotation (task -1.6, second source: SeaShips). Absolute-pixel
  boxes (no normalization); captures original source subclass per object
  for dataset-description purposes (not used for filtering, since this
  project treats SeaShips purely as a visual-appearance source for the
  target's single class); flags (does not abort on) XML/image dimension
  mismatches. `scripts/extrair_seaships.py` chains: zip extraction →
  Roboflow-augmentation dedup (-1.3) → VOC crop extraction → unified filter
  → Drive copy — dedup runs before extraction to avoid processing
  near-identical augmented copies. Covered by `tests/test_extrair_crops_voc.py`
  (4 tests) — all passing. Full suite: 41/41 passing.
- `src/extraction/extrair_crops_csv_abo.py`: crop extraction from
  ABOShips' CSV annotation (task -1.6, third source). Indexes all 9,880
  images by base filename across 16 date subfolders before processing the
  CSV (CSV references filenames without subfolder or extension); detects
  ambiguous base filenames across subfolders (`NomeBaseAmbiguo`); groups
  CSV rows by filename to support multiple boxes per image; cross-checks
  the CSV's `width`/`height` columns against the derived bbox dimensions
  (confirmed numerically that these columns are box dimensions, not image
  dimensions — matches a suspicion documented, now unverified claims
  replaced with direct confirmation). Deliberately does NOT hardcode the
  "images are always 1280×720" assumption seen in prior documentation —
  always reads real image dimensions instead, verified only on a 5-image
  sample. `scripts/extrair_aboships.py` chains extraction + unified filter
  + Drive copy. Covered by `tests/test_extrair_crops_csv_abo.py`
  (6 tests) — all passing. Full suite: 47/47 passing. This completes task
  -1.6's code for all three public crop sources (SMD, SeaShips, ABOShips);
  none of the three extraction scripts has been run against real data yet.
- `src/materialize/collapse_classes.py`: multi-class-to-single-class label
  collapse (task -1.8, UA-DETRAC — 4 original classes: bus/car/truck/van).
  Distinct from `materializar_labels_final` (which only validates a single
  class, doesn't convert). Detects unexpected class ids
  (`ClasseOriginalInesperada`). `scripts/preparar_ua_detrac.py` chains:
  zip extraction → class collapse (train + valid) → Roboflow dedup (train,
  100/9,816 duplicates found) → `labels_final/` materialization of the
  valid split (composition background, per the same §5.2 rule of never
  using the split used for detector fitting) → vehicle crop pool
  extraction from the deduplicated train split → unified filter → Drive
  copy. No new extractor needed — reuses `extrair_crops_de_yolo` and the
  existing filter/materialization modules. Covered by
  `tests/test_collapse_classes.py` (3 tests) — all passing. Full suite:
  50/50 passing. **This completes Phase -1** (tasks -1.1 through -1.9, all
  coded and tested; none of the four source-extraction scripts has been
  run against real Drive data yet — pending task 0.2's `min_dim_px`
  decision).
- `src/profiling/target_profile.py`: canonical structural profiling (task
  0.1, start of Phase 0). Reimplements from scratch (ports the validated
  METHOD, not the legacy artifact) the letterbox-correct COCO-style
  small/medium/large classification that resolves the previously diagnosed
  71.6%-vs-82.2% discrepancy. `scripts/perfilar_citra.py` runs it against
  CITRA-3D-Real's materialized `labels_final/`. Covered by
  `tests/test_target_profile.py` (5 tests, including a numerical
  reproduction of the letterbox-vs-stretch divergence on an 80×80px box in
  a 1920×1080 image) — all passing. Full suite: 55/55 passing.

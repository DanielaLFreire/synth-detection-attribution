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

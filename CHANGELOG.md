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

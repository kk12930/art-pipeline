
2026-04-18: `python -m unittest discover -v` was misleading because it returned 0 tests until `tests/__init__.py` existed. The targeted module invocation is still the clearest verification command.

2026-04-18: Added `python scripts/phase1_checks.py` as a tiny repeatable wrapper for the three documented Phase 1 checks; it runs from repo root and does not trigger real SDXL generation by default.

2026-04-18: README device docs were aligned to `scripts/generate_sdxl.py`: `--device auto` is the only fallback path, while explicit `--device cuda` fails if CUDA is unavailable and does not recover to CPU automatically.

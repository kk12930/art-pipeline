2026-04-18: Added a minimal root `config.yaml` with only `defaults` plus an empty `presets` mapping so the config file stays human-editable and future preset support has a stable place to live.

2026-04-18: Kept `scripts/generate_sdxl.py` single-image only and applied config defaults only when explicit CLI flags are absent, preserving the current override model.
# Decisions: Phase 2 Documentation
- Updated README to reflect Phase 2 status.
- Included specific examples for CLI overrides of presets.
- Defined clear precedence rules in the README to prevent user confusion.
2026-04-18: F4 scope fidelity review approved — current Phase 2 remains limited to config defaults, named resolution presets, CLI precedence, tests, and README docs; no batch, LoRA/adapter, API/server, or queueing logic was introduced, and the single-image CLI save path is still intact.

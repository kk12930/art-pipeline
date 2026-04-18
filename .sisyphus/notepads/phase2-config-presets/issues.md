2026-04-18: `--prompt` had to be made optional in argparse so config defaults could supply it; otherwise the loader existed but could never satisfy a missing prompt.

2026-04-18: Returning both `defaults` and `presets` from `load_config()` keeps the config shape future-proof for preset support without introducing preset selection yet.

2026-04-18: F1 audit review: Phase 2 is mostly aligned and remains single-image only, but the shipped root `config.yaml` omits a default `prompt` even though the plan and README describe prompt-capable config defaults as part of the Phase 2 goal.

2026-04-18 Manual CLI QA (F3): --help succeeds; real CLI rejects missing prompt when root config lacks defaults.prompt; patched main() run confirmed config-supplied prompt plus preset/CLI merge without triggering a model download; unknown preset fails with explicit available-preset list.

2026-04-18 review: REJECT for F2 pending a fix to CLI precedence detection; apply_config_defaults/apply_resolution_preset only treat separate tokens like --width 900 as explicit CLI overrides, so valid argparse forms like --width=900 are overwritten by config defaults or presets.

2026-04-18 fix note: explicit-flag detection now treats both `--flag value` and `--flag=value` as overrides, and the shipped `config.yaml` now includes a default prompt so the config-supplied prompt path works from the real CLI.

2026-04-18 F1 retry audit: APPROVE on current repo state — root `config.yaml` now includes a default prompt, `generate_sdxl.py` preserves explicit CLI overrides including `--flag=value`, tests cover config prompt + precedence behavior, README matches the shipped config/preset flow, and the implementation remains single-image only and within Phase 2 scope.

2026-04-18 retry review: APPROVE for F2. The previous --flag=value precedence blocker is fixed via argument_was_provided(), regression coverage now asserts equals-sign CLI override precedence in main(), PyYAML is listed in requirements.txt, and the shipped config/docs now align on config-supplied prompt behavior.

2026-04-18 Manual CLI QA retry (F3): current root config now supplies defaults.prompt on the visible CLI surface; --help succeeds; unknown preset still fails explicitly; safe patched main() runs confirmed shipped config defaults and --height=512 precedence over preset without requiring a model download.

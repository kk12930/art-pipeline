2026-04-18: `yaml.safe_load()` is available in the environment, so the config loader can stay tiny and avoid custom parsing logic.

2026-04-18: The current test suite already covers the one-image save path; adding a small config-load test was enough to prove the new default settings are readable without widening scope.

2026-04-18: Preset resolution fits cleanly as a narrow overlay: config defaults set width/height first, `--preset` fills only missing dimensions, and explicit CLI flags still win.

2026-04-18: Fresh-setup completeness depends on listing PyYAML in requirements, and README should show the shipped config prompt so the documented no-`--prompt` path matches the real repo state.

- Added regression coverage proving CLI --width/--height override both config defaults and selected presets.
# Learnings: Phase 2 Config & Presets
- CLI precedence logic: CLI args > Presets > Config defaults.
- Configuration schema: Supports defaults mapping and presets mapping.
- Documentation: README now reflects Phase 2 status and usage examples.
Documentation consistency fix: Updated README.md to match the actual config.yaml state. Removed non-existent 'portrait' and 'landscape' presets from examples and replaced with 'square'.

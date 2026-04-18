# Phase 2 Config Presets

## TL;DR

> **Quick Summary**: Add configuration-file driven prompt defaults and resolution presets on top of the existing Phase 1 single-image SDXL baseline.
>
> **Deliverables**:
> - A small config file for default generation parameters
> - Named resolution presets usable from the CLI
> - CLI behavior that supports config defaults plus explicit argument overrides
> - Tests and docs for the new config/preset flow
>
> **Estimated Effort**: Small-Medium
> **Parallel Execution**: YES - 2 waves
> **Critical Path**: Task 1 -> Task 2 -> Task 4 -> Final Verification

---

## Context

### Original Request
After finishing Phase 1, the next step should be the smallest useful Phase 2 increment: make prompt/resolution configurable without jumping into batch generation, LoRA, or API work.

### Working Interpretation
Phase 2 is intentionally narrow:
- Add a config file for reusable default prompt settings and generation parameters
- Add a preset mechanism for named width/height pairs
- Let CLI arguments override config values
- Keep generation scope to one image per command invocation

### Scope Boundaries
- INCLUDE: config file, resolution presets, CLI/config merge behavior, docs, tests
- EXCLUDE: batch generation, LoRA loading, API/server layer, queueing, prompt templating engines

---

## Work Objectives

### Core Objective
Turn the current direct-argument Phase 1 script into a config-aware single-image generator with reusable named resolution presets.

### Definition of Done
- [ ] A config file exists with default generation settings and named size presets
- [ ] The CLI can load defaults from config and still accept explicit overrides
- [ ] Tests cover config loading and preset resolution behavior
- [ ] README explains how to use config defaults and size presets

### Must Have
- Preserve single-image generation workflow
- Keep config format simple and human-editable
- Keep CLI explicit and predictable
- Verify override precedence with tests

### Must NOT Have
- No batch job lists
- No LoRA/model adapter logic
- No API or background service
- No broad architecture expansion

---

## TODOs

- [x] 1. Add a minimal config file and loader for default generation settings
- [x] 2. Add named resolution preset support to the CLI with override precedence
- [x] 3. Expand tests for config parsing, preset lookup, and CLI-overrides-config behavior
- [x] 4. Update README with config and preset usage examples

---

## Final Verification Wave

- [x] F1. Plan compliance audit
- [x] F2. Code quality review
- [x] F3. Manual CLI QA
- [x] F4. Scope fidelity check

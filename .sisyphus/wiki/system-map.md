---
title: System Map
status: current
last_verified: 2026-04-18
---

# System Map

## Current truth

这个仓库当前是一个 **本地优先的 SDXL CLI 项目**，已经演进到 Phase 4：

- `config.yaml` 提供全局默认值与命名分辨率 preset。
- `scripts/generate_sdxl.py` 是单图 / batch / LoRA 推理的主入口。
- `tests/test_generate_sdxl.py` 是行为契约，覆盖 config、preset、CLI precedence、device、batch、LoRA。
- `README.md` 提供用户面运行与验证说明。
- `.sisyphus/plans/` 和 `.sisyphus/notepads/` 保存计划、问题、决策、经验。

## How the repository is organized

### 1. Human-facing docs

- `README.md`
  - 说明当前 phase、验证流程、配置/preset 规则、batch 和 LoRA 用法。
  - 适合作为外部说明入口，但不应单独被视为唯一真相。

### 2. Runtime truth

- `config.yaml`
  - 当前默认 prompt、model、negative prompt、宽高、steps、guidance scale、seed。
  - 当前仅内置 `square` preset。

- `scripts/generate_sdxl.py`
  - `parse_args()`：CLI surface。
  - `load_config()`：读取 `config.yaml`。
  - `apply_config_defaults()`：在 CLI 未显式提供时注入 config defaults。
  - `apply_resolution_preset()`：在 CLI 未显式给出宽高时应用 preset。
  - `apply_batch_item_overrides()`：批量模式下插入 batch item 这一层覆盖。
  - `resolve_device()`：处理 `auto` / `cpu` / `cuda`。
  - `apply_lora_weights()`：加载本地 LoRA 权重。

### 3. Verification truth

- `tests/test_generate_sdxl.py`
  - 证明显式 CLI 参数（包括 `--flag=value` 形式）覆盖 config/preset。
  - 证明 config prompt 可作为 prompt 来源。
  - 证明 unknown preset 会显式失败。
  - 证明 batch 是顺序执行且 fail-fast。
  - 证明 LoRA 路径必须存在。

- `scripts/phase1_checks.py`
  - 固化最小验证组合：discover tests、定向测试、CLI help。

### 4. History and rationale

- `.sisyphus/plans/phase2-config-presets.md`
  - 记录阶段目标和完成标准。

- `.sisyphus/notepads/phase2-config-presets/issues.md`
  - 记录 `--prompt` 可选化、`--flag=value` precedence 回归、README/config 对齐问题。

- `.sisyphus/notepads/phase2-config-presets/decisions.md`
  - 记录“只在 CLI 未显式提供参数时才应用 config defaults”等关键决定。

- `.sisyphus/notepads/phase2-config-presets/learnings.md`
  - 记录 preset overlay、PyYAML 依赖、README 一致性等经验。

## Source-of-truth hierarchy

1. **代码与测试**：`scripts/generate_sdxl.py` + `tests/test_generate_sdxl.py`
2. **运行时配置**：`config.yaml`
3. **用户文档**：`README.md`
4. **历史上下文**：`.sisyphus/plans/` + `.sisyphus/notepads/`
5. **本 wiki**：派生总结层，不反向覆盖上面任何来源

## How to verify

1. 读 `config.yaml`，确认当前默认 prompt/model/preset。
2. 读 `scripts/generate_sdxl.py`，确认 precedence、device、batch、LoRA 逻辑。
3. 读 `tests/test_generate_sdxl.py`，确认行为是否被测试锁定。
4. 跑 `python scripts/phase1_checks.py` 做最小冒烟验证。

## Known failure modes

- README 与实际 `config.yaml` 漂移时，文档会误导使用者。
- 如果只读 README 不读测试，很容易遗漏 `--flag=value` 这类细节行为。
- 如果直接把 notepads 当最终真相，会把历史问题和当前行为混在一起。

## Canonical sources

- `README.md`
- `config.yaml`
- `scripts/generate_sdxl.py`
- `scripts/phase1_checks.py`
- `tests/test_generate_sdxl.py`
- `.sisyphus/notepads/phase2-config-presets/issues.md`
- `.sisyphus/notepads/phase2-config-presets/decisions.md`
- `.sisyphus/notepads/phase2-config-presets/learnings.md`

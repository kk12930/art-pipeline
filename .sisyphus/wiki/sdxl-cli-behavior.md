---
title: SDXL CLI Behavior
status: current
last_verified: 2026-04-18
---

# SDXL CLI Behavior

## Current truth

当前主入口是 `scripts/generate_sdxl.py`，支持：

- 单图生成
- `batch.yaml` 顺序批量生成
- 可选本地 LoRA 权重加载
- `config.yaml` 默认值与命名分辨率 preset

### Parameter precedence

当前优先级是：

#### 单图模式

1. 显式 CLI 参数
2. preset
3. `config.yaml` defaults
4. 脚本默认值

#### batch 模式

1. 显式 CLI 参数
2. batch item 字段
3. preset
4. `config.yaml` defaults
5. 脚本默认值

这里的“显式 CLI 参数”同时包括：

- `--width 900`
- `--width=900`

因为 `argument_was_provided()` 同时识别这两种形式。

### Prompt behavior

- `parse_args()` 中 `--prompt` 默认是 `None`。
- `apply_config_defaults()` 会在 CLI 未显式提供 prompt 时尝试从 `config.yaml` 的 `defaults.prompt` 填充。
- 如果最终仍没有 prompt，`ensure_prompt()` 会抛出：
  - `A prompt is required either on the CLI or in config.yaml defaults.`

### Preset behavior

- 当前 `config.yaml` 只有一个 `square` preset。
- `apply_resolution_preset()` 只负责 `width` 和 `height`。
- 如果用户显式传了 `--width` 或 `--height`，preset 对应维度不会覆盖它。
- unknown preset 会抛出包含可用 preset 列表的 `ValueError`。

### Device behavior

- `--device auto`：CUDA 可用时用 `cuda`，否则用 `cpu`
- `--device cpu`：固定 CPU
- `--device cuda`：要求 CUDA 可用；不可用时直接报错，不会自动回退

### Dtype behavior

- 解析后 device 为 `cuda` 时，dtype 用 `torch.float16`
- 否则用 `torch.float32`

### Batch behavior

- batch 是**顺序执行**，不是并发系统。
- 当前是 **fail-fast**：任一 item 报错，后续 item 不再执行。
- 运行时会复用同一个已经构建好的 pipeline。

### LoRA behavior

- `--lora-path` 是可选参数。
- 如果路径不存在，`apply_lora_weights()` 会抛 `FileNotFoundError`。
- 如果路径存在，LoRA 会在 pipeline 构建后、生成前加载一次。
- 当前不支持多 LoRA、adapter 命名、LoRA scale、按 item 切换 LoRA。

### Output behavior

- 默认输出目录是 `outputs/`
- 文件名前缀：
  - 单图：`sdxl_...png`
  - batch：`sdxl_001_...png` 这类带序号前缀

## How to verify

### Minimal checks

```bash
python -m unittest tests.test_generate_sdxl -v
python scripts/generate_sdxl.py --help
```

### Behavior-specific checks

- config prompt 生效：直接运行 `python scripts/generate_sdxl.py`
- preset 生效：`python scripts/generate_sdxl.py --preset square`
- CLI 覆盖 preset：`python scripts/generate_sdxl.py --preset square --height=512`
- batch 覆盖路径：`python scripts/generate_sdxl.py --batch-file batch.yaml --width=900 --height=600`
- LoRA 路径检查：传一个存在/不存在的本地文件各验证一次

## Known test evidence

- `test_main_prefers_cli_dimensions_over_config_and_preset_with_equals_sign`
- `test_main_uses_preset_when_cli_does_not_override_resolution`
- `test_main_uses_config_prompt_when_cli_prompt_missing`
- `test_main_raises_for_unknown_preset`
- `test_main_runs_batch_items_with_fail_fast`
- `test_main_batch_respects_cli_dimensions_over_batch_item`
- `test_apply_lora_weights_raises_for_missing_path`
- `test_main_loads_lora_before_generation`

## Known failure modes

- `config.yaml` 缺失 `defaults.prompt` 且 CLI 也没传 prompt 时，生成前会失败。
- 使用不存在的 preset 会显式失败。
- 使用 `--device cuda` 但本机 CUDA 不可用会直接失败。
- batch 中任意 item 抛错会中断整个批次。
- `--lora-path` 指向不存在文件时会直接失败。

## Historical notes

- `issues.md` 记录过一个关键回归：早期只识别 `--width 900`，没有正确识别 `--width=900`，导致 config/preset 错误覆盖显式 CLI 值。
- `learnings.md` 明确总结了 preset overlay 逻辑：config 先填默认值，preset 只补缺失维度，CLI 永远优先。

## Canonical sources

- `config.yaml`
- `scripts/generate_sdxl.py`
- `tests/test_generate_sdxl.py`
- `README.md`
- `.sisyphus/notepads/phase2-config-presets/issues.md`
- `.sisyphus/notepads/phase2-config-presets/learnings.md`

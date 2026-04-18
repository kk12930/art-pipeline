---
title: Debugging Playbook
status: current
last_verified: 2026-04-18
---

# Debugging Playbook

## Current truth

这个项目的排障入口应当先走 **验证流**，再定位到 config / CLI / runtime / batch / LoRA 的具体层面。

推荐顺序：

1. 先跑测试
2. 再看 CLI surface
3. 最后做手动生成检查

这与 `README.md` 和 `scripts/phase1_checks.py` 一致。

## How to verify

### Canonical verification flow

```bash
python -m unittest discover -v
python -m unittest tests.test_generate_sdxl -v
python scripts/generate_sdxl.py --help
```

也可以直接运行：

```bash
python scripts/phase1_checks.py
```

### Manual generation checks

CPU 路径：

```bash
python scripts/generate_sdxl.py --prompt "A simple sketch" --device cpu
```

GPU 路径：

```bash
python scripts/generate_sdxl.py --prompt "A serene mountain landscape" --device cuda
```

成功信号：终端出现 `Saved image to:`，并且输出目录新增 PNG。

## Triage map

### 1. CLI 参数看起来没生效

先检查：

- 是否是 `--flag=value` 形式
- 是否被 batch item、preset 或 config defaults 覆盖
- 是否看错了单图和 batch 两套 precedence

优先读：

- `scripts/generate_sdxl.py` 中的 `argument_was_provided()`
- `apply_config_defaults()`
- `apply_resolution_preset()`
- `apply_batch_item_overrides()`

相关测试：

- `test_main_prefers_cli_dimensions_over_config_and_preset_with_equals_sign`
- `test_main_batch_respects_cli_dimensions_over_batch_item`

### 2. 没传 prompt 就报错

先检查：

- 根目录 `config.yaml` 是否存在
- `defaults.prompt` 是否存在
- 运行目录是否正确（`load_config()` 默认从 `Path.cwd() / "config.yaml"` 读）

相关来源：

- `ensure_prompt()`
- `test_main_uses_config_prompt_when_cli_prompt_missing`

### 3. preset 不生效或报 unknown preset

先检查：

- `config.yaml` 中是否真的存在该 preset
- preset 名称是否拼写正确
- 是否显式传了 `--width` / `--height`，导致 preset 被局部覆盖

相关测试：

- `test_main_uses_preset_when_cli_does_not_override_resolution`
- `test_main_raises_for_unknown_preset`

### 4. `--device cuda` 失败

先检查：

- 本机 CUDA 是否可用
- 是否本来应该用 `--device auto`

当前行为不是自动回退；显式指定 `cuda` 就要求 CUDA 一定存在。

相关测试：

- `test_resolve_device_auto_uses_cuda_when_available`
- `test_resolve_device_auto_falls_back_to_cpu_when_cuda_unavailable`
- `test_resolve_device_cuda_raises_when_unavailable`

### 5. batch 中途停了

这通常不是 bug，而是当前设计：**fail-fast**。

先检查：

- 第一个失败 item 的 prompt / preset / LoRA / output_dir 参数
- 该 item 是否依赖不存在的文件或不支持的字段

相关测试：

- `test_main_runs_batch_items_with_fail_fast`
- `test_main_batch_stops_on_first_error`

### 6. LoRA 加载失败

先检查：

- 路径是否存在
- 路径是否是本地文件
- 是否在 pipeline 构建后才调用加载逻辑

相关测试：

- `test_apply_lora_weights_loads_existing_path`
- `test_apply_lora_weights_raises_for_missing_path`
- `test_main_loads_lora_before_generation`

## Known failure modes

- `--prompt` 曾经在 argparse 中被设为必填，导致 config 默认 prompt 路径形同虚设；此问题已修复。
- `--flag=value` 曾经不被当作显式 CLI override；此问题已修复并有回归测试。
- README 与 shipped config/preset 状态曾发生漂移；维护时要同步检查文档与实际配置。

## Practical rule of thumb

- **先看测试，再看 README。** README 讲“应该怎样用”，测试更接近“实际被锁定的行为”。
- **先确认运行目录，再怀疑配置。** `load_config()` 默认从当前工作目录找 `config.yaml`。
- **先确认是否显式传参，再判断 precedence 异常。** 很多问题其实是 override 层级理解错了。

## Canonical sources

- `README.md`
- `scripts/phase1_checks.py`
- `scripts/generate_sdxl.py`
- `tests/test_generate_sdxl.py`
- `.sisyphus/notepads/phase2-config-presets/issues.md`
- `.sisyphus/notepads/phase2-config-presets/decisions.md`
- `.sisyphus/notepads/phase2-config-presets/learnings.md`

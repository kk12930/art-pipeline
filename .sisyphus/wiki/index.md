---
title: LLM Wiki Index
status: current
last_verified: 2026-04-18
---

# LLM Wiki Index

这个目录是 **派生知识层**：用于沉淀当前稳定行为、验证路径和调试结论。

- 代码与配置真相仍以 `scripts/`, `config.yaml`, `tests/`, `README.md` 为准。
- 历史计划、问题、决策仍以 `.sisyphus/plans/` 与 `.sisyphus/notepads/` 为准。
- 这里不记录原始过程，而是整理出当前可复用的工程知识。

## 当前页面

- [system-map](./system-map.md) — 仓库里哪些文件是权威来源、它们如何连接。
- [sdxl-cli-behavior](./sdxl-cli-behavior.md) — 当前 CLI、配置、Preset、batch、LoRA 的稳定行为。
- [debugging-playbook](./debugging-playbook.md) — 验证顺序、常见失败模式、排障入口。

## 维护规则

1. 只在行为经过验证后更新本目录。
2. 页面优先总结“当前真相”，不要直接复制完整原始日志。
3. 每次更新都要回链到权威来源文件。
4. 如果 README、脚本、测试不一致，优先标出冲突，不自行脑补。

## 当前关注主题

- 配置优先级：CLI > batch item > preset > config defaults > script defaults
- prompt 来源与缺失时的失败行为
- device 解析：`auto` / `cpu` / `cuda`
- LoRA 最小接入行为
- 最小验证流与已知回归点

## Canonical sources

- `README.md`
- `config.yaml`
- `scripts/generate_sdxl.py`
- `scripts/phase1_checks.py`
- `tests/test_generate_sdxl.py`
- `.sisyphus/notepads/phase2-config-presets/{issues,decisions,learnings}.md`

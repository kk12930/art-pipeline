# art-pipeline

从最小可运行版本开始。当前处于 **Phase 5: 最小 API 接口** 阶段。

## 阶段目标
- 支持通过 `config.yaml` 管理全局默认参数。
- 支持命名分辨率预设（Presets）。
- 建立清晰的参数优先级机制（CLI > Preset > Config）。
- 支持通过 `batch.yaml` 顺序批量生成。
- 保持 CLI 单图/批量两种用法都稳定。
- 支持通过可选 `--lora-path` 加载本地 LoRA 权重进行推理。
- 支持一个最小本地 FastAPI 接口用于单图生成。

## 环境安装

本仓库依赖特定的本地基线，请确保在符合条件的 Python 环境下安装。

在 VSCode 中打开仓库后，请先选择与你实际运行 `python -m unittest discover -v` 和 `python scripts/generate_sdxl.py --help` 时一致的 Python 解释器，再运行编辑器检查。
如果 Pylance 报出看起来偏严格的提示，优先确认解释器是否选对，而不是直接关闭检查。

```bash
# 1. 确保已激活本地虚拟环境
# 2. 安装经确认的依赖版本
pip install -r requirements.txt
```

### 确认的依赖基线
- `torch 2.11.0+cu130`
- `torchvision 0.26.0+cu130`
- `diffusers`, `transformers`, `accelerate` (详见 requirements.txt)

## OpenCode / Superpowers 增强

本仓库推荐使用 OpenCode 配合 Superpowers 插件以获得最佳开发体验。

### 1. 插件配置
确保项目根目录下存在 `opencode.json` 文件，并包含以下配置：

```json
{
  "plugin": [
    "superpowers@git+https://github.com/obra/superpowers.git"
  ]
}
```

### 2. 重启与验证
添加配置后，必须**重启 OpenCode** 才能使插件生效。

重启后，必须通过以下步骤验证 Skill 发现情况（不可直接假设 Skill 已可用）：
1. 在聊天框中调用 `skill` 工具。
2. 确认输出中列出了 Superpowers 相关的 Skill。

**注意：** 如果 Skill 未显示，请检查网络环境并尝试再次重启。

### 3. 迭代执行工作流
在 Phase 1 阶段，建议遵循以下迭代循环以确保高质量交付：

1.  **Plan (规划)**: 明确任务目标。阅读 `.sisyphus/plans/` 下的相关计划文件，理清待办事项。可以使用对话或文档记录具体的设计决策。
2.  **Execute (执行)**: 按照计划执行最小粒度的代码修改或环境配置。保持原子性，避免一次性引入过多变更。
3.  **Test/Verify (验证)**: 每次修改后立即运行验证。
    *   运行 `python scripts/phase1_checks.py` 进行基础功能冒烟测试。
    *   运行相关单元测试：`python -m unittest tests.test_generate_sdxl -v`。
    *   如有必要，进行手动生成检查（区分 CPU/GPU 路径）。
4.  **Review (复核)**: 在继续下一个任务前，对当前变更进行审视。
    *   如果已安装 Superpowers，调用 `review-work` 等相关 Skill。
    *   如果 Skill 不可用，手动对照预期结果进行检查，并在 `.sisyphus/notepads/` 下记录发现或决策。
5.  **Continue (继续)**: 完成一个闭环后，更新待办列表，转向下一个原子任务。

## 运行指南

### 1. Canonical verification flow

先跑测试，再看 CLI 帮助，最后按硬件环境做手动生成检查。

#### a) 发现式测试
```bash
python -m unittest discover -v
```
成功信号：所有测试都显示 `ok`，最后以 `OK` 结束。

#### b) 定向脚本测试
```bash
python -m unittest tests.test_generate_sdxl -v
```
成功信号：仅输出 `tests.test_generate_sdxl` 相关用例，并且全部通过，没有 error 或 failure。

#### c) CLI 帮助验证
```bash
python scripts/generate_sdxl.py --help
```
成功信号：命令正常退出，输出包含 `--prompt`、`--device`、`--output-dir` 等参数说明。

### 2. Manual generation checks

#### CPU 路径
适用于无 GPU、只想强制走 CPU、或做最保守本地验证的情况。
```bash
python scripts/generate_sdxl.py --prompt "A simple sketch" --device cpu
```
成功信号：命令正常结束，终端打印 `Saved image to:`，并且 `outputs/` 下新增一个 PNG 文件。

#### GPU 路径
仅适用于本机 CUDA 环境可用的情况；`--device cuda` 不会自动回退到 CPU。
```bash
python scripts/generate_sdxl.py --prompt "A serene mountain landscape" --device cuda
```
成功信号：命令正常结束，终端打印 `Saved image to:`，并且 `outputs/` 下新增一个 PNG 文件。
如果 CUDA 不可用，这条命令会直接失败，而不是自动切换到 CPU。

### 3. Test/verify summary

Phase 5 的最小验证组合就是：
- `python -m unittest discover -v`
- `python -m unittest tests.test_generate_sdxl -v`
- `python -m unittest tests.test_api -v`
- `python scripts/generate_sdxl.py --help`

### 4. Minimal API (Phase 5)

当前新增的是一个**最小本地 FastAPI 接口**，用于在本机通过 HTTP 调用单图生成逻辑。它不是生产级服务，不包含认证、任务队列、数据库或后台 worker。

#### 启动方式

```bash
python -m uvicorn api.server:app --host 127.0.0.1 --port 8000
```

#### 健康检查

```bash
curl http://127.0.0.1:8000/health
```

成功信号：返回

```json
{"status":"ok"}
```

#### 单图生成请求

```bash
curl -X POST http://127.0.0.1:8000/generate \
  -H "Content-Type: application/json" \
  -d "{\"prompt\":\"A simple sketch icon\",\"device\":\"cpu\",\"output_dir\":\"outputs\"}"
```

成功信号：返回 JSON，包含保存后的文件路径，例如：

```json
{"outputPath":"outputs/sdxl_20260418_120000.png"}
```

#### 当前 API 范围

- 仅提供 `GET /health`
- 仅提供 `POST /generate`
- 当前 API 复用与 CLI 相同的配置加载、preset、LoRA、输出保存逻辑
- 当前只暴露**单图生成**接口，不直接暴露 batch.yaml 批量接口
- 当前建议仅绑定到 `127.0.0.1` 本地使用

## 配置与预设 (Phase 2)

本阶段引入了 `config.yaml` 配置文件，允许开发者自定义默认参数并使用命名分辨率预设。

### 1. 配置文件结构 (`config.yaml`)

项目根目录下的 `config.yaml` 包含两个主要部分：

- `defaults`: 设置所有生成的全局默认值（如 `model`, `steps`, `guidance_scale` 等）。
- `presets`: 定义命名的分辨率组合（`width` 和 `height`）。
- 当前仓库自带的 `config.yaml` 也包含一个可直接使用的默认 `prompt`，因此不传 `--prompt` 时会先尝试读取配置中的提示词。

```yaml
defaults:
  prompt: A clean product-style icon on a neutral background.
  model: stabilityai/stable-diffusion-xl-base-1.0
  negative_prompt: blurry, low quality, distorted, text, watermark
  width: 1024
  height: 1024
  steps: 30
  guidance_scale: 7.0
  seed: null

presets:
  square:
    width: 1024
    height: 1024
```

### 2. 参数优先级 (Precedence)

脚本在解析参数时遵循以下优先级顺序（从高到低）：

1.  **显式 CLI 参数**: 命令行中直接指定的参数（如 `--width 512`）。
2.  **预设 (Preset)**: 通过 `--preset` 指定的命名配置中的参数。
3.  **配置默认值 (Config Defaults)**: `config.yaml` 中 `defaults` 部分的定义。
4.  **脚本硬编码默认值**: 脚本代码中定义的初始默认值。

**核心逻辑：** 显式 CLI 参数永远具有最高优先级，即使指定了预设，手动传入的 `--width` 或 `--height` 也会覆盖预设中的对应值。

### 3. 使用示例

#### 使用配置文件默认值
如果 `config.yaml` 中已配置 `prompt`（仓库默认就是如此），直接运行：
```bash
python scripts/generate_sdxl.py --prompt "A futuristic city"
```

也可以省略 `--prompt`，直接使用 `config.yaml` 的默认提示词：
```bash
python scripts/generate_sdxl.py
```

#### 使用预设 (Preset)
```bash
python scripts/generate_sdxl.py --prompt "A fantasy forest" --preset square
```

#### 预设与 CLI 覆盖
使用 `square` 预设但临时修改高度：
```bash
python scripts/generate_sdxl.py --prompt "Sunset beach" --preset square --height 512
```
在此示例中，宽度将遵循 `square` 预设（如 1024），而高度将被强制设为 512。

## 批量生成 (Phase 3)

本阶段在原有单图 CLI 基础上增加了最小批量能力。当前仍然是 **CLI 项目**，不是 API 或后台服务；批量执行通过 `batch.yaml` 顺序驱动。

### 1. `batch.yaml` 结构

项目当前支持的最小批量结构如下：

```yaml
items:
  - prompt: A clean mobile app icon
    preset: square
  - prompt: A dashboard hero illustration
    width: 1280
    height: 720
    steps: 40
```

每个批量条目当前可用字段：
- `prompt`
- `negative_prompt`
- `width`
- `height`
- `preset`
- `steps`
- `guidance_scale`
- `seed`
- `output_dir`

### 2. 批量命令行用法

```bash
python scripts/generate_sdxl.py --batch-file batch.yaml --device cpu
```

也可以继续用 CLI 显式参数覆盖批量条目中的分辨率：

```bash
python scripts/generate_sdxl.py --batch-file batch.yaml --width 900 --height 600 --device cpu
```

### 3. 批量模式下的优先级

批量模式沿用现有参数合并思路，但在单个批量条目层面再插入一层：

1. **显式 CLI 参数**
2. **批量条目字段**
3. **Preset**
4. **Config Defaults**
5. **脚本硬编码默认值**

也就是说：
- CLI 仍然拥有最高优先级
- 单个批量条目可以覆盖 `config.yaml` 的默认值
- 批量条目如果只写 `preset`，就会使用对应 preset 的宽高

### 4. 当前批量执行策略

- 当前是**顺序执行**，不是并发任务系统
- 当前是**失败即停止（fail-fast）**：任意一条生成报错，整个 batch 立即停止
- 当前默认会复用同一个已加载的 pipeline 来顺序执行批量条目
- 当前仍然只保存到本地 `outputs/`（或你传入的 `--output-dir`）

## LoRA 推理 (Phase 4)

本阶段在已有单图 / 批量 CLI 基础上，增加了最小 LoRA 推理接入。当前只支持**本地 LoRA 权重文件加载**，不涉及训练、服务化或复杂多适配器管理。

### 1. CLI 用法

单图 + LoRA：

```bash
python scripts/generate_sdxl.py --prompt "A polished game icon" --lora-path models/example-lora.safetensors --device cpu
```

批量 + LoRA：

```bash
python scripts/generate_sdxl.py --batch-file batch.yaml --lora-path models/example-lora.safetensors --device cpu
```

### 2. 当前行为

- `--lora-path` 是**可选参数**
- 当前要求它指向一个**本地存在的文件路径**
- 如果路径不存在，脚本会直接报错并停止
- 当前会在 pipeline 构建完成后加载一次 LoRA，然后继续单图或 batch 推理
- 当前没有做多 LoRA 组合、adapter 命名或 LoRA scale 调整

### 3. 作用范围

当前 LoRA 接入属于最小推理版本，只解决：

- 如何把本地 LoRA 权重接入现有 SDXL CLI
- 如何在当前单图 / batch 流程中复用同一个已加载的 LoRA pipeline

当前还没有覆盖：

- 多 LoRA 切换
- 每个 batch item 不同 LoRA
- LoRA scale 配置
- Refiner / ControlNet 组合

## 说明
- 默认生成结果保存至 `outputs/` 目录；它只用于本地生成产物，不应提交到版本库。
- `--device auto` 会在 CUDA 可用时使用 CUDA，否则使用 CPU。
- `--device cuda` 要求 CUDA 环境可用；脚本不会在该模式下自动回退到 CPU。
- 脚本目前不支持显存不足时的自动退避或优化。

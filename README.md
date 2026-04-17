# art-pipeline

Clean slate.

This repository has been reset and will be rebuilt from the first stage.

```
art-pipeline/
├── configs/
│   ├── icon_preset.yaml          # Icon 生成预设（尺寸、prompt 模板、负面提示词）
│   ├── ui_design_preset.yaml     # UI 设计图生成预设
│   ├── model_config.yaml         # 模型路径配置
│   └── lora_training.yaml        # LoRA 训练配置
├── core/
│   ├── generator.py              # 图片生成核心引擎（SDXL + LoRA）
│   ├── presets.py                # 预设管理器
│   ├── prompt_builder.py         # 提示词构建器
│   ├── decomposer.py             # UI 拆解引擎（SAM 分割 + 元素分类）
│   ├── post_processor.py         # 后处理引擎（超分、标准化、批量导出）
│   └── training/
│       └── data_prep.py          # 训练数据准备
├── scripts/
│   ├── generate.py               # CLI 生成入口
│   ├── train_lora.py             # LoRA 训练脚本
│   ├── decompose.py              # CLI 拆解入口
│   └── setup_models.py           # 环境检查与模型下载指引
├── training_data/
│   ├── raw/                      # 原始参考图
│   └── processed/                # 处理后的训练数据
├── models/
│   ├── lora/                     # 训练好的 LoRA 权重
│   └── sam/                      # SAM 模型权重
├── outputs/                      # 生成结果
├── requirements.txt
├── README.md
└── .gitignore
```

---

## 开发路线图

详见 [项目总览 Issue #1](https://github.com/kk12930/art-pipeline/issues/1)

| 阶段 | 内容 | 状态 |
|------|------|------|
| 阶段一 | 核心生成能力（SDXL + LoRA 推理） | 🚧 进行中 |
| 阶段二 | 自定义风格训练（LoRA 微调） | 📅 计划中 |
| 阶段三 | UI 设计图自动拆解（SAM 分割） | 📅 计划中 |
| 阶段四 | 后处理与优化（超分、标准化） | 📅 计划中 |
| 阶段五 | 可视化界面（Gradio） | 📅 计划中 |

---

## 常见问题

**Q: 显存不足怎么办？**
> 编辑 `configs/model_config.yaml`，确保所有显存优化选项均为 `true`。
> 生成时降低分辨率（如 768x768 替代 1024x1024）。

**Q: 模型下载太慢？**
> 设置 HuggingFace 镜像：
> ```bash
> export HF_ENDPOINT=https://hf-mirror.com
> ```

**Q: SAM 分割效果不好？**
> 尝试使用更高精度的模型（vit_h > vit_l > vit_b），
> 或手动调整 `UIDecomposer` 中 `SamAutomaticMaskGenerator` 的参数。

---

## License

MIT

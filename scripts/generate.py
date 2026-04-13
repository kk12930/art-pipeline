"""
CLI 图片生成入口
支持 Icon 和 UI 设计图的命令行批量生成
"""

import argparse
import os
import sys
from pathlib import Path

# 将项目根目录加入 sys.path，确保能正确导入 core 模块
_PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

import yaml
from PIL import Image


def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="美术资源生成工具 —— 基于 SDXL + LoRA",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 生成一个剑的游戏图标（medium 尺寸）
  python scripts/generate.py "a shining sword" --type icon --size medium --seed 42

  # 生成 UI 设计图（手机竖屏）
  python scripts/generate.py "fantasy RPG main menu" --type ui_design --size mobile_portrait

  # 使用自定义 LoRA 批量生成 3 张
  python scripts/generate.py "fire mage icon" --lora models/lora/fire_style.safetensors --batch 3
""",
    )
    parser.add_argument("prompt", type=str, help="图片描述（核心提示词）")
    parser.add_argument(
        "--type", "-t",
        type=str,
        default="icon",
        choices=["icon", "ui_design"],
        help="生成类型：icon（图标）或 ui_design（UI设计图），默认 icon",
    )
    parser.add_argument(
        "--size", "-s",
        type=str,
        default=None,
        help="输出尺寸名称（如 small/medium/large/hd 或 mobile_portrait），默认使用预设第一个尺寸",
    )
    parser.add_argument(
        "--lora", "-l",
        type=str,
        default=None,
        help="LoRA 权重文件路径（可选）",
    )
    parser.add_argument(
        "--lora-weight",
        type=float,
        default=0.8,
        help="LoRA 强度，范围 0.0~1.0，默认 0.8",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="随机种子，不指定则随机生成",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="outputs",
        help="输出目录，默认 outputs/",
    )
    parser.add_argument(
        "--batch", "-b",
        type=int,
        default=1,
        help="批量生成数量，默认 1",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=30,
        help="推理步数，默认 30",
    )
    parser.add_argument(
        "--cfg",
        type=float,
        default=7.5,
        help="CFG 引导强度，默认 7.5",
    )
    parser.add_argument(
        "--negative", "-n",
        type=str,
        default=None,
        help="额外的负面提示词（会与预设负面提示词合并）",
    )
    return parser.parse_args()


def main() -> None:
    """主函数：加载模型、构建提示词、生成并保存图片"""
    args = parse_args()

    # 延迟导入重型依赖，确保 --help 等操作不受影响
    try:
        from core.generator import ArtGenerator
    except ImportError as exc:
        print(f"[错误] 缺少依赖：{exc}")
        print("请先安装核心依赖: pip install torch diffusers transformers accelerate safetensors")
        sys.exit(1)

    from core.presets import PresetManager
    from core.prompt_builder import PromptBuilder

    # 加载模型配置
    model_config_path = _PROJECT_ROOT / "configs" / "model_config.yaml"
    if not model_config_path.exists():
        print(f"[错误] 模型配置文件不存在: {model_config_path}")
        sys.exit(1)
    with open(model_config_path, "r", encoding="utf-8") as f:
        model_config = yaml.safe_load(f)

    # 加载预设
    preset = PresetManager()
    preset.load(args.type)

    # 确定输出尺寸
    if args.size:
        width, height = preset.get_size(args.size)
    else:
        # 默认使用内部生成分辨率（之后可按需 resize）
        width, height = preset.get_internal_resolution()

    # 构建提示词
    builder = PromptBuilder()
    full_prompt = builder.build(preset._data.get("prompt_template", "{prompt}"), args.prompt)
    full_negative = builder.merge_negative(preset.negative_prompt, args.negative)

    print(f"[信息] 正向提示词: {full_prompt[:80]}...")
    print(f"[信息] 负向提示词: {full_negative[:80]}...")

    # 初始化生成器并加载模型
    generator = ArtGenerator(model_config)
    generator.load_model()

    # 加载 LoRA（可选）
    if args.lora:
        generator.load_lora(args.lora, args.lora_weight)

    # 确保输出目录存在
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 获取内部生成分辨率（SDXL 推理分辨率）
    internal_w, internal_h = preset.get_internal_resolution()

    # 批量生成
    for i in range(args.batch):
        seed = args.seed if args.seed is not None else None
        if args.batch > 1 and args.seed is not None:
            seed = args.seed + i  # 批量时递增种子，保证多样性

        print(f"\n[信息] 生成第 {i + 1}/{args.batch} 张...")
        image = generator.generate(
            prompt=full_prompt,
            negative_prompt=full_negative,
            width=internal_w,
            height=internal_h,
            steps=args.steps,
            guidance_scale=args.cfg,
            seed=seed,
        )

        # Resize 到目标输出尺寸
        if (internal_w, internal_h) != (width, height):
            image = image.resize((width, height), Image.Resampling.LANCZOS)
            print(f"[信息] 已 Resize 到目标尺寸: {width}x{height}")

        # 保存图片
        suffix = f"_{i + 1:03d}" if args.batch > 1 else ""
        seed_str = f"_seed{seed}" if seed is not None else ""
        filename = f"{args.type}_{args.prompt[:20].replace(' ', '_')}{seed_str}{suffix}.png"
        out_path = out_dir / filename
        image.save(str(out_path))
        print(f"[信息] 已保存: {out_path}")

    print(f"\n✅ 生成完成！共 {args.batch} 张图片，保存在 {out_dir}/")


if __name__ == "__main__":
    main()

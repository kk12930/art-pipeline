#!/usr/bin/env python3
# scripts/generate.py
# CLI 图片生成入口
# 支持 Icon 和 UI 设计图的批量生成

import argparse
import sys
import os
from pathlib import Path

# 确保项目根目录在 Python 路径中
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.generator import ArtGenerator
from core.presets import PresetManager
from core.prompt_builder import PromptBuilder
import yaml


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="美术工业管线 - 图片生成工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 生成中等尺寸的金色宝剑图标
  python scripts/generate.py "金色宝剑" --type icon --size medium

  # 生成高清图标，使用自定义 LoRA 和固定种子
  python scripts/generate.py "蓝色魔法按钮" --type icon --size hd --lora models/lora/mystyle.safetensors --seed 42

  # 生成移动端 UI 设计图，批量 3 张
  python scripts/generate.py "奇幻风格主界面" --type ui_design --size mobile_portrait --batch 3

  # 指定输出目录
  python scripts/generate.py "红色药水图标" --type icon --output outputs/icons/
        """,
    )

    parser.add_argument("prompt", type=str, help="生成提示词（描述要生成的内容）")
    parser.add_argument(
        "--type",
        type=str,
        choices=["icon", "ui_design"],
        default="icon",
        help="生成类型：icon（图标）或 ui_design（UI 设计图）。默认: icon",
    )
    parser.add_argument(
        "--size",
        type=str,
        default=None,
        help=(
            "导出尺寸预设名称。\n"
            "  icon 可用: small(64), medium(128), large(256), hd(512)\n"
            "  ui_design 可用: mobile_portrait(1080x1920), mobile_landscape(1920x1080), ipad(2048x1536)\n"
            "  不指定时仅保存内部生成分辨率的原始图片"
        ),
    )
    parser.add_argument(
        "--lora",
        type=str,
        default=None,
        help="LoRA 权重文件路径（.safetensors）",
    )
    parser.add_argument(
        "--lora-weight",
        type=float,
        default=0.8,
        dest="lora_weight",
        help="LoRA 权重系数，范围 0.0~1.0。默认: 0.8",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="随机种子（设置后可复现相同结果）。默认: 随机",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=None,
        help="去噪步数。默认使用预设值（icon: 30，ui_design: 35）",
    )
    parser.add_argument(
        "--cfg",
        type=float,
        default=None,
        dest="guidance_scale",
        help="提示词引导强度（CFG scale）。默认使用预设值",
    )
    parser.add_argument(
        "--negative",
        type=str,
        default="",
        help="额外的负面提示词",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="outputs",
        help="输出目录路径。默认: outputs/",
    )
    parser.add_argument(
        "--batch",
        type=int,
        default=1,
        help="批量生成数量。默认: 1",
    )
    parser.add_argument(
        "--no-resize",
        action="store_true",
        help="跳过导出尺寸缩放，仅保存内部生成分辨率的图片",
    )

    return parser.parse_args()


def load_model_config() -> dict:
    """加载模型配置文件"""
    config_path = Path(__file__).parent.parent / "configs" / "model_config.yaml"
    if not config_path.exists():
        print(f"[Warning] 模型配置文件不存在: {config_path}，使用默认配置")
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def main():
    args = parse_args()

    print("=" * 60)
    print("🎨 美术工业管线 - 图片生成")
    print("=" * 60)
    print(f"  类型: {args.type}")
    print(f"  提示词: {args.prompt}")
    print(f"  尺寸: {args.size or '内部分辨率'}")
    print(f"  批量: {args.batch}")
    print(f"  种子: {args.seed or '随机'}")
    if args.lora:
        print(f"  LoRA: {args.lora} (weight={args.lora_weight})")
    print()

    # 加载预设和模型配置
    preset_manager = PresetManager()
    prompt_builder = PromptBuilder()
    model_config = load_model_config()

    # 构建完整提示词
    full_prompt = preset_manager.build_prompt(args.type, args.prompt)
    preset_negative = preset_manager.get_negative_prompt(args.type)
    full_negative = prompt_builder.merge_negative(preset_negative, args.negative)

    # 获取内部生成分辨率
    gen_width, gen_height = preset_manager.get_internal_size(args.type)

    # 获取生成参数（命令行参数优先于预设默认值）
    preset_defaults = preset_manager.get_defaults(args.type)
    steps = args.steps or preset_defaults.get("steps", 30)
    guidance_scale = args.guidance_scale or preset_defaults.get("guidance_scale", 7.5)

    # 初始化生成器并加载模型
    generator = ArtGenerator(model_config)
    generator.load_model()

    # 加载 LoRA（如指定）
    if args.lora:
        generator.load_lora(args.lora, args.lora_weight)
    elif model_config.get("default_lora"):
        generator.load_lora(model_config["default_lora"], model_config.get("default_lora_weight", 0.8))

    # 创建输出目录
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 批量生成
    generated_files = []
    for i in range(args.batch):
        seed = args.seed if args.seed is not None else None
        if args.batch > 1 and args.seed is not None:
            seed = args.seed + i  # 批量时种子递增

        print(f"\n[{i+1}/{args.batch}] 正在生成...")
        image = generator.generate(
            prompt=full_prompt,
            negative_prompt=full_negative,
            width=gen_width,
            height=gen_height,
            steps=steps,
            guidance_scale=guidance_scale,
            seed=seed,
        )

        # 保存原始生成图片
        import time
        timestamp = int(time.time())
        raw_filename = f"{args.type}_{timestamp}_{i:02d}_raw.png"
        raw_path = output_dir / raw_filename
        image.save(str(raw_path))
        generated_files.append(str(raw_path))
        print(f"  已保存原始图片: {raw_path}")

        # 按指定尺寸导出
        if args.size and not args.no_resize:
            from core.post_processor import PostProcessor
            processor = PostProcessor()
            target_w, target_h = preset_manager.get_size(args.type, args.size)

            if args.type == "icon":
                # 图标使用标准化方法（居中+padding）
                standardized = processor.standardize_icon(image, target_size=target_w)
                sized_filename = f"{args.type}_{timestamp}_{i:02d}_{args.size}.png"
                sized_path = output_dir / sized_filename
                standardized.save(str(sized_path))
                generated_files.append(str(sized_path))
                print(f"  已保存 {args.size} 尺寸图标: {sized_path}")
            else:
                # UI 设计图直接缩放到目标尺寸
                resized = image.resize((target_w, target_h))
                sized_filename = f"{args.type}_{timestamp}_{i:02d}_{args.size}.png"
                sized_path = output_dir / sized_filename
                resized.save(str(sized_path))
                generated_files.append(str(sized_path))
                print(f"  已保存 {args.size} 尺寸图片: {sized_path}")

    print(f"\n✅ 生成完成！共 {len(generated_files)} 个文件")
    print(f"   输出目录: {output_dir.resolve()}")


if __name__ == "__main__":
    main()

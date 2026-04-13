#!/usr/bin/env python3
# scripts/train_lora.py
# 一键 LoRA 训练脚本
# 负责数据预处理，并生成/打印 kohya_ss 训练命令

import argparse
import sys
import os
from pathlib import Path

# 确保项目根目录在 Python 路径中
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.training.data_prep import DataPreparer
import yaml


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="美术工业管线 - LoRA 训练工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 使用默认配置训练（从 training_data/raw/ 读取数据）
  python scripts/train_lora.py --name mystyle_v1

  # 指定数据目录和配置文件
  python scripts/train_lora.py --name mystyle_v1 --data-dir my_images/ --config configs/lora_training.yaml

  # 自定义触发词
  python scripts/train_lora.py --name mystyle_v1 --trigger-word "gamestyle"
        """,
    )

    parser.add_argument(
        "--name",
        type=str,
        required=True,
        help="LoRA 模型名称（用于命名输出文件，如 mystyle_v1）",
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="training_data/raw",
        dest="data_dir",
        help="原始训练数据目录。默认: training_data/raw/",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="models/lora",
        dest="output_dir",
        help="LoRA 权重输出目录。默认: models/lora/",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="configs/lora_training.yaml",
        help="LoRA 训练配置文件路径。默认: configs/lora_training.yaml",
    )
    parser.add_argument(
        "--trigger-word",
        type=str,
        default=None,
        dest="trigger_word",
        help="LoRA 触发词（不指定时从配置文件读取，默认为 'mystyle'）",
    )
    parser.add_argument(
        "--target-size",
        type=int,
        default=1024,
        dest="target_size",
        help="训练图片分辨率（正方形边长）。默认: 1024",
    )
    parser.add_argument(
        "--skip-prep",
        action="store_true",
        dest="skip_prep",
        help="跳过数据预处理（数据已经准备好时使用）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        dest="dry_run",
        help="仅打印训练命令，不实际执行",
    )

    return parser.parse_args()


def load_training_config(config_path: str) -> dict:
    """加载训练配置文件"""
    path = Path(config_path)
    if not path.exists():
        print(f"[Warning] 配置文件不存在: {path}，使用默认参数")
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def generate_kohya_command(
    name: str,
    processed_dir: str,
    output_dir: str,
    config: dict,
    trigger_word: str,
) -> str:
    """
    生成 kohya_ss sd_scripts 的训练命令。

    Args:
        name: LoRA 名称。
        processed_dir: 处理后的训练数据目录。
        output_dir: 输出目录。
        config: 训练配置字典。
        trigger_word: 触发词。

    Returns:
        完整的 accelerate launch 训练命令字符串。
    """
    training = config.get("training", {})
    lora = config.get("lora", {})
    mem_opt = config.get("memory_optimization", {})
    data = config.get("data", {})

    # 构建命令参数
    cmd_parts = [
        "accelerate launch --num_cpu_threads_per_process=1",
        "  kohya_ss/train_network.py",
        f"  --pretrained_model_name_or_path=stabilityai/stable-diffusion-xl-base-1.0",
        f"  --train_data_dir={processed_dir}",
        f"  --output_dir={output_dir}",
        f"  --output_name={name}",
        f"  --resolution={data.get('resolution', 1024)},{data.get('resolution', 1024)}",
        f"  --train_batch_size={training.get('batch_size', 1)}",
        f"  --gradient_accumulation_steps={training.get('gradient_accumulation', 4)}",
        f"  --learning_rate={training.get('learning_rate', 1e-4)}",
        f"  --lr_scheduler={training.get('lr_scheduler', 'cosine')}",
        f"  --lr_warmup_steps={training.get('lr_warmup_steps', 100)}",
        f"  --max_train_epochs={training.get('epochs', 20)}",
        f"  --network_module=networks.lora",
        f"  --network_dim={lora.get('rank', 32)}",
        f"  --network_alpha={lora.get('alpha', 16)}",
        f"  --dataset_repeats={data.get('dataset_repeats', 10)}",
        f"  --save_every_n_epochs={config.get('save', {}).get('save_every_n_epochs', 5)}",
        f"  --caption_extension=.txt",
    ]

    # 可选优化项
    if mem_opt.get("fp16"):
        cmd_parts.append("  --mixed_precision=fp16")
    if mem_opt.get("cache_latents"):
        cmd_parts.append("  --cache_latents")
    if mem_opt.get("gradient_checkpointing"):
        cmd_parts.append("  --gradient_checkpointing")
    if mem_opt.get("use_8bit_adam"):
        cmd_parts.append("  --optimizer_type=AdamW8bit")
    if data.get("flip_augmentation"):
        cmd_parts.append("  --flip_aug")

    return " \\\n".join(cmd_parts)


def main():
    args = parse_args()

    print("=" * 60)
    print("🏋️  美术工业管线 - LoRA 训练")
    print("=" * 60)
    print(f"  LoRA 名称: {args.name}")
    print(f"  数据目录: {args.data_dir}")
    print(f"  输出目录: {args.output_dir}")
    print(f"  配置文件: {args.config}")
    print()

    # 加载训练配置
    config = load_training_config(args.config)

    # 触发词优先级：命令行 > 配置文件 > 默认值
    trigger_word = args.trigger_word or config.get("trigger_word", "mystyle")
    print(f"  触发词: {trigger_word}")
    print()

    # 处理后数据目录
    processed_dir = str(Path(args.data_dir).parent / "processed")

    # 步骤 1：数据预处理
    if not args.skip_prep:
        print("📁 步骤 1/3：数据预处理")
        print("-" * 40)
        preparer = DataPreparer(
            raw_dir=args.data_dir,
            processed_dir=processed_dir,
        )
        processed = preparer.prepare(target_size=args.target_size)
        if not processed:
            print("❌ 数据预处理失败，请检查原始数据目录")
            sys.exit(1)
        preparer.auto_caption(trigger_word=trigger_word)
        result = preparer.verify()
        if result.get("missing_captions"):
            print("⚠️  部分图片缺少 caption，训练可能受影响")
        print()
    else:
        print("📁 步骤 1/3：跳过数据预处理（--skip-prep）\n")

    # 步骤 2：验证 kohya_ss 是否可用
    print("🔍 步骤 2/3：检查 kohya_ss 环境")
    print("-" * 40)
    kohya_path = Path("kohya_ss")
    if not kohya_path.exists():
        print("⚠️  未找到 kohya_ss 目录，请先克隆：")
        print("  git clone https://github.com/kohya-ss/sd-scripts.git kohya_ss")
        print("  cd kohya_ss && pip install -r requirements.txt")
        print()
    else:
        print("✓ 找到 kohya_ss 目录")
        print()

    # 步骤 3：生成训练命令
    print("🚀 步骤 3/3：训练命令")
    print("-" * 40)
    train_cmd = generate_kohya_command(
        name=args.name,
        processed_dir=processed_dir,
        output_dir=args.output_dir,
        config=config,
        trigger_word=trigger_word,
    )

    print("请在项目根目录执行以下命令开始训练：\n")
    print(train_cmd)
    print()

    if not args.dry_run and kohya_path.exists():
        import subprocess
        print("▶️  正在启动训练...")
        try:
            subprocess.run(train_cmd, shell=True, check=True)
            print(f"\n✅ 训练完成！LoRA 权重已保存到: {args.output_dir}/{args.name}.safetensors")
        except subprocess.CalledProcessError as e:
            print(f"❌ 训练失败: {e}")
            sys.exit(1)
    elif args.dry_run:
        print("（--dry-run 模式，仅打印命令，未实际执行）")
    else:
        print("（请先安装 kohya_ss 后重新运行）")


if __name__ == "__main__":
    main()

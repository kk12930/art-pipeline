"""
LoRA 训练一键脚本
调用 DataPreparer 预处理数据，并输出 kohya_ss 训练命令
"""

import argparse
import subprocess
import sys
from pathlib import Path

# 将项目根目录加入 sys.path
_PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

import yaml

from core.training.data_prep import DataPreparer


def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="LoRA 训练一键脚本（数据预处理 + 训练命令生成）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 使用默认配置训练
  python scripts/train_lora.py --name my_style

  # 指定数据目录和配置文件
  python scripts/train_lora.py --name fire_style --data-dir ./my_refs --config configs/lora_training.yaml
""",
    )
    parser.add_argument(
        "--name", "-n",
        type=str,
        required=True,
        help="LoRA 名称（用于输出文件命名）",
    )
    parser.add_argument(
        "--data-dir", "-d",
        type=str,
        default=None,
        help="原始参考图目录，默认 training_data/raw/",
    )
    parser.add_argument(
        "--config", "-c",
        type=str,
        default=None,
        help="LoRA 训练配置文件路径，默认 configs/lora_training.yaml",
    )
    parser.add_argument(
        "--target-size",
        type=int,
        default=1024,
        help="训练图片目标尺寸（正方形边长），默认 1024",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="是否直接调用 subprocess 执行训练（需要已安装 kohya_ss）",
    )
    return parser.parse_args()


def build_kohya_command(config: dict, lora_name: str) -> list[str]:
    """
    根据配置字典构建 kohya_ss 训练命令

    Args:
        config:    lora_training.yaml 中的配置字典
        lora_name: LoRA 名称（覆盖配置中的 output_name）

    Returns:
        命令行参数列表
    """
    cmd = [
        "python",
        "train_network.py",  # kohya_ss 的训练脚本路径
        f"--pretrained_model_name_or_path={config.get('pretrained_model', 'stabilityai/stable-diffusion-xl-base-1.0')}",
        f"--train_data_dir={config.get('train_data_dir', 'training_data/processed/')}",
        f"--output_dir={config.get('output_dir', 'models/lora/')}",
        f"--output_name={lora_name}",
        f"--resolution={config.get('resolution', 1024)}",
        f"--train_batch_size={config.get('train_batch_size', 1)}",
        f"--gradient_accumulation_steps={config.get('gradient_accumulation_steps', 4)}",
        f"--learning_rate={config.get('learning_rate', 1e-4)}",
        f"--lr_scheduler={config.get('lr_scheduler', 'cosine')}",
        f"--max_train_epochs={config.get('max_train_epochs', 20)}",
        f"--save_every_n_epochs={config.get('save_every_n_epochs', 5)}",
        f"--network_module={config.get('network_module', 'networks.lora')}",
        f"--network_dim={config.get('network_dim', 32)}",
        f"--network_alpha={config.get('network_alpha', 16)}",
        f"--mixed_precision={config.get('mixed_precision', 'fp16')}",
    ]
    if config.get("cache_latents"):
        cmd.append("--cache_latents")
    if config.get("gradient_checkpointing"):
        cmd.append("--gradient_checkpointing")

    return cmd


def main() -> None:
    """主函数：预处理数据，打印或执行 kohya_ss 训练命令"""
    args = parse_args()

    # 确定配置文件路径
    config_path = Path(args.config) if args.config else _PROJECT_ROOT / "configs" / "lora_training.yaml"
    if not config_path.exists():
        print(f"[错误] 配置文件不存在: {config_path}")
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        lora_config = yaml.safe_load(f)

    # === 步骤 1: 数据预处理 ===
    print("=" * 60)
    print("步骤 1/2：预处理训练数据")
    print("=" * 60)
    raw_dir = args.data_dir or str(_PROJECT_ROOT / "training_data" / "raw")
    processed_dir = str(_PROJECT_ROOT / "training_data" / "processed")

    preparer = DataPreparer(raw_dir=raw_dir, processed_dir=processed_dir)
    processed = preparer.prepare(target_size=args.target_size)
    preparer.auto_caption()

    if not processed:
        print(f"[警告] 未找到可处理的图片，请将参考图放入 {raw_dir}/")
        print("  支持格式：.jpg .jpeg .png .webp .bmp")

    # === 步骤 2: 生成/执行训练命令 ===
    print("\n" + "=" * 60)
    print("步骤 2/2：LoRA 训练")
    print("=" * 60)

    cmd = build_kohya_command(lora_config, args.name)

    print("\n[信息] 生成的 kohya_ss 训练命令：")
    print("  " + " \\\n    ".join(cmd))
    print()

    if args.run:
        print("[信息] 正在调用 subprocess 执行训练命令...")
        try:
            subprocess.run(cmd, check=True)
            print("\n✅ LoRA 训练完成！")
        except FileNotFoundError:
            print(
                "[错误] 找不到 train_network.py，请确认已安装 kohya_ss 并将其加入 PATH\n"
                "  安装参考: https://github.com/kohya-ss/sd-scripts"
            )
            sys.exit(1)
        except subprocess.CalledProcessError as exc:
            print(f"[错误] 训练失败，返回码: {exc.returncode}")
            sys.exit(exc.returncode)
    else:
        print(
            "💡 提示：添加 --run 参数可直接执行训练命令（需要已安装 kohya_ss）\n"
            "  或复制上方命令手动执行"
        )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# scripts/decompose.py
# CLI UI 拆解入口
# 对 UI 设计图进行自动分割和元素导出

import argparse
import sys
from pathlib import Path

# 确保项目根目录在 Python 路径中
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.decomposer import UIDecomposer, ElementType
import yaml


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="美术工业管线 - UI 设计图自动拆解工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 拆解 UI 图片，输出到 outputs/decomposed/ 目录
  python scripts/decompose.py ui_design.png

  # 指定输出目录
  python scripts/decompose.py ui_design.png --output outputs/my_ui_elements/

  # 仅导出特定类型的元素（如只导出图标和角标）
  python scripts/decompose.py ui_design.png --types ICON BADGE

  # 指定 SAM 权重路径
  python scripts/decompose.py ui_design.png --sam-checkpoint models/sam/sam_vit_h_4b8939.pth
        """,
    )

    parser.add_argument("image_path", type=str, help="输入 UI 图片路径（PNG/JPG）")
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="输出目录路径。默认: outputs/decomposed/{图片名}/",
    )
    parser.add_argument(
        "--sam-checkpoint",
        type=str,
        default=None,
        dest="sam_checkpoint",
        help="SAM 模型权重路径。默认从 configs/model_config.yaml 读取",
    )
    parser.add_argument(
        "--sam-type",
        type=str,
        default="vit_h",
        choices=["vit_h", "vit_l", "vit_b"],
        dest="sam_type",
        help="SAM 模型类型。默认: vit_h（最高精度）",
    )
    parser.add_argument(
        "--types",
        type=str,
        nargs="+",
        default=None,
        choices=[t.name for t in ElementType],
        help="只导出指定类型的元素。不指定时导出所有元素",
    )
    parser.add_argument(
        "--min-area",
        type=float,
        default=0.0,
        dest="min_area",
        help="最小面积比例阈值（0.0~1.0），过滤过小的元素。默认: 0.0（不过滤）",
    )
    parser.add_argument(
        "--no-background",
        action="store_true",
        dest="no_background",
        help="不导出背景元素",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="仅打印分割结果摘要，不导出图片文件",
    )

    return parser.parse_args()


def load_model_config() -> dict:
    """加载模型配置文件"""
    config_path = Path(__file__).parent.parent / "configs" / "model_config.yaml"
    if not config_path.exists():
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def main():
    args = parse_args()

    image_path = Path(args.image_path)
    if not image_path.exists():
        print(f"❌ 图片不存在: {image_path}")
        sys.exit(1)

    # 确定输出目录
    if args.output:
        output_dir = Path(args.output)
    else:
        output_dir = Path("outputs") / "decomposed" / image_path.stem

    print("=" * 60)
    print("🔪 美术工业管线 - UI 图片自动拆解")
    print("=" * 60)
    print(f"  输入图片: {image_path}")
    print(f"  输出目录: {output_dir}")
    print()

    # 确定 SAM 权重路径（命令行 > 配置文件）
    model_config = load_model_config()
    sam_checkpoint = args.sam_checkpoint or model_config.get("sam_checkpoint", "models/sam/sam_vit_h_4b8939.pth")
    sam_type = args.sam_type or model_config.get("sam_model_type", "vit_h")

    # 初始化拆解器
    decomposer = UIDecomposer(sam_checkpoint=sam_checkpoint, model_type=sam_type)

    # 执行拆解
    try:
        elements = decomposer.decompose(str(image_path))
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("\n请安装必要依赖后重试（参见 scripts/setup_models.py）")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 拆解失败: {e}")
        sys.exit(1)

    # 过滤元素
    filtered_elements = elements

    # 过滤面积过小的元素
    if args.min_area > 0:
        filtered_elements = [e for e in filtered_elements if e.area_ratio >= args.min_area]
        print(f"  面积过滤（>= {args.min_area:.1%}）后剩余: {len(filtered_elements)} 个元素")

    # 过滤背景
    if args.no_background:
        filtered_elements = [e for e in filtered_elements if e.type != ElementType.BACKGROUND]

    # 过滤指定类型
    if args.types:
        target_types = {ElementType[t] for t in args.types}
        filtered_elements = [e for e in filtered_elements if e.type in target_types]
        print(f"  类型过滤（{args.types}）后剩余: {len(filtered_elements)} 个元素")

    # 打印摘要
    print()
    print("📊 拆解结果摘要：")
    print("-" * 40)
    type_counts = {}
    for elem in elements:
        type_counts[elem.type.name] = type_counts.get(elem.type.name, 0) + 1
    for type_name, count in sorted(type_counts.items()):
        print(f"  {type_name:<15} × {count}")
    print(f"  {'合计':<15}  {len(elements)}")

    if args.summary:
        print("\n（--summary 模式，不导出文件）")
        return

    # 导出元素
    if not filtered_elements:
        print("\n⚠️  没有符合条件的元素需要导出")
        return

    print(f"\n💾 正在导出 {len(filtered_elements)} 个元素到 {output_dir}...")
    exported = decomposer.export_all(filtered_elements, str(output_dir))

    print(f"\n✅ 拆解完成！")
    print(f"   共导出 {len(exported)} 个元素")
    print(f"   输出目录: {output_dir.resolve()}")


if __name__ == "__main__":
    main()

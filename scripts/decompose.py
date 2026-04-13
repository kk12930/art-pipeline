"""
CLI UI 拆解入口
对输入图片进行自动分割和元素分类，并批量导出各元素
"""

import argparse
import sys
from pathlib import Path

# 将项目根目录加入 sys.path
_PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

import yaml

from core.decomposer import UIDecomposer


def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="UI 设计图自动拆解工具（基于 SAM 分割）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 拆解一张 UI 截图，导出到默认目录
  python scripts/decompose.py assets/ui_screenshot.png

  # 指定输出目录
  python scripts/decompose.py assets/ui_screenshot.png --output outputs/decomposed/
""",
    )
    parser.add_argument(
        "image_path",
        type=str,
        help="要拆解的 UI 图片路径",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="元素导出目录，默认在 outputs/<图片名>_decomposed/",
    )
    parser.add_argument(
        "--sam-checkpoint",
        type=str,
        default=None,
        help="SAM 模型权重路径，默认读取 configs/model_config.yaml 中的配置",
    )
    return parser.parse_args()


def main() -> None:
    """主函数：加载图片，运行拆解，导出元素"""
    args = parse_args()

    # 验证输入图片
    image_path = Path(args.image_path)
    if not image_path.exists():
        print(f"[错误] 图片文件不存在: {image_path}")
        sys.exit(1)

    # 确定 SAM checkpoint 路径（优先使用命令行参数，其次读 model_config.yaml）
    sam_checkpoint = args.sam_checkpoint
    if not sam_checkpoint:
        model_config_path = _PROJECT_ROOT / "configs" / "model_config.yaml"
        if model_config_path.exists():
            with open(model_config_path, "r", encoding="utf-8") as f:
                model_config = yaml.safe_load(f)
            sam_checkpoint = model_config.get("sam_checkpoint", "models/sam/sam_vit_h.pth")
        else:
            sam_checkpoint = "models/sam/sam_vit_h.pth"

    # 确定输出目录
    if args.output:
        output_dir = args.output
    else:
        output_dir = str(_PROJECT_ROOT / "outputs" / f"{image_path.stem}_decomposed")

    print(f"[信息] 输入图片: {image_path}")
    print(f"[信息] SAM 权重: {sam_checkpoint}")
    print(f"[信息] 输出目录: {output_dir}")

    # 执行拆解
    decomposer = UIDecomposer(sam_checkpoint=sam_checkpoint)
    try:
        elements = decomposer.decompose(str(image_path))
    except ImportError as exc:
        print(f"\n[错误] {exc}")
        print("\n请先安装拆解功能所需依赖：")
        print("  pip install numpy opencv-python")
        print(
            "  pip install git+https://github.com/facebookresearch/segment-anything.git"
        )
        sys.exit(1)

    if not elements:
        print("[警告] 未检测到任何元素")
        sys.exit(0)

    # 打印拆解结果摘要
    print(f"\n{'=' * 50}")
    print(f"拆解结果（共 {len(elements)} 个元素）：")
    print(f"{'类型':<15} {'面积占比':>8} {'置信度':>8} {'边界框'}")
    print("-" * 50)
    for elem in elements:
        bbox_str = f"({elem.bbox[0]},{elem.bbox[1]},{elem.bbox[2]},{elem.bbox[3]})"
        print(
            f"{elem.type.value:<15} {elem.area_ratio:>7.1%} {elem.confidence:>8.2f}  {bbox_str}"
        )
    print("=" * 50)

    # 导出所有元素
    saved = decomposer.export_all(elements, output_dir)
    print(f"\n✅ 拆解完成！{len(saved)} 个元素已保存到 {output_dir}/")


if __name__ == "__main__":
    main()

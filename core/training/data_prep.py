"""
训练数据准备模块
负责将原始参考图批量裁剪、缩放到统一尺寸，并生成对应的 caption 文件
"""

import os
from pathlib import Path
from typing import List, Optional, Tuple

from PIL import Image


# 支持的图片扩展名
_IMG_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

# 默认原始图目录和处理后输出目录
_RAW_DIR = Path(__file__).parent.parent.parent / "training_data" / "raw"
_PROCESSED_DIR = Path(__file__).parent.parent.parent / "training_data" / "processed"


class DataPreparer:
    """
    训练数据准备器
    将原始参考图批量处理为统一尺寸，并生成 caption 文件，供 LoRA 训练使用
    """

    def __init__(
        self,
        raw_dir: Optional[str] = None,
        processed_dir: Optional[str] = None,
    ):
        """
        初始化数据准备器

        Args:
            raw_dir:       原始参考图目录，默认 training_data/raw/
            processed_dir: 处理后输出目录，默认 training_data/processed/
        """
        self.raw_dir = Path(raw_dir) if raw_dir else _RAW_DIR
        self.processed_dir = Path(processed_dir) if processed_dir else _PROCESSED_DIR

    def prepare(self, target_size: int = 1024) -> List[str]:
        """
        批量裁剪缩放参考图到统一尺寸，并生成同名 caption 文件

        Caption 文件为 .txt，内容为空（供手动填写或由 auto_caption 填写）

        Args:
            target_size: 目标正方形边长（像素），默认 1024

        Returns:
            处理后的图片路径列表
        """
        if not self.raw_dir.exists():
            raise FileNotFoundError(f"原始图目录不存在: {self.raw_dir}")

        self.processed_dir.mkdir(parents=True, exist_ok=True)

        # 收集所有支持的图片文件
        image_files = [
            f for f in self.raw_dir.iterdir()
            if f.suffix.lower() in _IMG_EXTENSIONS
        ]

        if not image_files:
            print(f"[警告] 未在 {self.raw_dir} 找到任何图片文件")
            return []

        print(f"[信息] 找到 {len(image_files)} 张参考图，开始处理（目标尺寸: {target_size}x{target_size}）")

        processed_paths: List[str] = []
        for img_path in image_files:
            try:
                img = Image.open(img_path).convert("RGB")
                processed = self._center_crop_resize(img, target_size)

                # 保存处理后的图片
                out_img_path = self.processed_dir / img_path.name
                processed.save(str(out_img_path), "PNG")

                # 生成对应的空 caption 文件
                caption_path = self.processed_dir / (img_path.stem + ".txt")
                if not caption_path.exists():
                    caption_path.write_text("", encoding="utf-8")

                processed_paths.append(str(out_img_path))
                print(f"[信息] 已处理: {img_path.name} → {out_img_path.name}")

            except Exception as exc:
                print(f"[错误] 处理 {img_path.name} 时出错: {exc}")

        print(f"[信息] 数据准备完成，共处理 {len(processed_paths)} 张图片")
        return processed_paths

    def auto_caption(self) -> None:
        """
        自动标注占位方法
        当前版本打印提示信息，后续版本将接入大模型（如 BLIP-2、LLaVA）自动生成 caption

        使用方式：
          先运行 prepare() 生成图片和空 caption 文件，
          再运行本方法自动填充 caption（或手动编辑 .txt 文件）
        """
        txt_files = list(self.processed_dir.glob("*.txt"))
        if not txt_files:
            print("[提示] 未找到 caption 文件，请先运行 prepare() 生成训练数据")
            return

        # 统计空 caption 数量
        empty = [f for f in txt_files if f.read_text(encoding="utf-8").strip() == ""]
        print(
            f"[提示] auto_caption 功能尚未接入大模型，暂时跳过自动标注。\n"
            f"  共找到 {len(txt_files)} 个 caption 文件，其中 {len(empty)} 个为空。\n"
            f"  请手动编辑 {self.processed_dir}/*.txt，\n"
            f"  或等待后续版本接入 BLIP-2 / LLaVA 自动标注功能。"
        )

    def _center_crop_resize(self, img: Image.Image, size: int) -> Image.Image:
        """
        中心裁剪并缩放图片到指定正方形尺寸

        处理流程：
          1. 按短边缩放，使短边等于目标尺寸
          2. 从中心裁剪出正方形区域

        Args:
            img:  输入 PIL 图片（RGB）
            size: 目标正方形边长

        Returns:
            裁剪缩放后的正方形 PIL 图片
        """
        w, h = img.size

        # 按短边计算缩放比例
        scale = size / min(w, h)
        new_w = round(w * scale)
        new_h = round(h * scale)
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        # 从中心裁剪
        left = (new_w - size) // 2
        top = (new_h - size) // 2
        img = img.crop((left, top, left + size, top + size))

        return img

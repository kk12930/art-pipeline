# core/training/data_prep.py
# 训练数据准备模块
# 负责对原始参考图进行裁剪、缩放和自动标注，为 LoRA 训练做准备

import os
import shutil
from pathlib import Path
from typing import List, Optional

from PIL import Image


class DataPreparer:
    """
    训练数据准备器。

    将 training_data/raw/ 中的原始参考图处理为统一格式，
    输出到 training_data/processed/ 目录，供 kohya_ss 等训练工具使用。

    处理步骤：
    1. 读取原始图片（支持 JPG、PNG、WEBP 等常见格式）
    2. 等比缩放并居中裁剪到目标尺寸（默认 1024x1024）
    3. 保存为 PNG 格式（训练工具兼容性更好）
    4. 生成对应的 caption 文件（.txt）

    示例:
        preparer = DataPreparer(raw_dir="training_data/raw/", processed_dir="training_data/processed/")
        preparer.prepare(target_size=1024)
        preparer.auto_caption(trigger_word="mystyle")
    """

    # 支持的图片格式
    SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}

    def __init__(
        self,
        raw_dir: str = "training_data/raw",
        processed_dir: str = "training_data/processed",
    ):
        """
        初始化数据准备器。

        Args:
            raw_dir: 原始参考图目录路径。
            processed_dir: 处理后数据输出目录路径。
        """
        self.raw_dir = Path(raw_dir)
        self.processed_dir = Path(processed_dir)

    def _collect_images(self) -> List[Path]:
        """
        收集原始目录中所有支持格式的图片文件。

        Returns:
            图片文件路径列表。

        Raises:
            FileNotFoundError: 原始图片目录不存在时抛出。
        """
        if not self.raw_dir.exists():
            raise FileNotFoundError(f"原始图片目录不存在: {self.raw_dir}")

        images = [
            p for p in self.raw_dir.iterdir()
            if p.suffix.lower() in self.SUPPORTED_FORMATS
        ]
        return sorted(images)

    def _resize_and_crop(self, image: Image.Image, target_size: int) -> Image.Image:
        """
        等比缩放后居中裁剪到正方形目标尺寸。

        处理流程：
        1. 等比缩放，使短边等于 target_size
        2. 居中裁剪，取正方形区域

        Args:
            image: 输入图片。
            target_size: 目标尺寸（正方形边长，单位像素）。

        Returns:
            裁剪后的正方形图片。
        """
        w, h = image.size

        # 等比缩放，短边对齐目标尺寸
        scale = target_size / min(w, h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        resized = image.resize((new_w, new_h), Image.LANCZOS)

        # 居中裁剪
        left = (new_w - target_size) // 2
        top = (new_h - target_size) // 2
        right = left + target_size
        bottom = top + target_size
        return resized.crop((left, top, right, bottom))

    def prepare(self, target_size: int = 1024) -> List[str]:
        """
        批量处理原始参考图，裁剪缩放到统一尺寸后保存。

        Args:
            target_size: 目标图片尺寸（正方形边长，单位像素）。
                         SDXL LoRA 训练推荐使用 1024。

        Returns:
            处理后的图片文件路径列表。

        Raises:
            FileNotFoundError: 原始图片目录不存在时抛出。
        """
        image_paths = self._collect_images()
        if not image_paths:
            print(f"[DataPreparer] ⚠️  在 {self.raw_dir} 中未找到图片文件")
            return []

        self.processed_dir.mkdir(parents=True, exist_ok=True)
        print(f"[DataPreparer] 找到 {len(image_paths)} 张原始图片，开始处理...")

        processed_paths = []
        for idx, img_path in enumerate(image_paths):
            try:
                image = Image.open(img_path).convert("RGB")
                processed = self._resize_and_crop(image, target_size)

                # 保存为 PNG（训练工具兼容性更好）
                output_name = f"{idx:04d}_{img_path.stem}.png"
                output_path = self.processed_dir / output_name
                processed.save(str(output_path), "PNG")
                processed_paths.append(str(output_path))
                print(f"[DataPreparer] [{idx+1}/{len(image_paths)}] {img_path.name} → {output_name}")
            except Exception as e:
                print(f"[DataPreparer] ⚠️  处理失败 {img_path.name}: {e}")

        print(f"[DataPreparer] 数据准备完成，共处理 {len(processed_paths)} 张图片")
        return processed_paths

    def auto_caption(
        self,
        trigger_word: str = "mystyle",
        description: str = "",
    ) -> List[str]:
        """
        为处理后的图片自动生成 caption 文件（.txt）。

        Caption 格式：{trigger_word}, {description}
        例如：mystyle, game UI icon, vibrant colors

        注意：当前为占位实现，生成简单的模板 caption。
        后续版本计划接入大模型（BLIP2/LLaVA）进行智能描述。

        Args:
            trigger_word: LoRA 触发词，用于激活训练的风格。默认 "mystyle"。
            description: 额外的描述文字，追加到触发词后。为空时仅使用触发词。

        Returns:
            生成的 caption 文件路径列表。
        """
        processed_images = [
            p for p in self.processed_dir.iterdir()
            if p.suffix.lower() == ".png"
        ]

        if not processed_images:
            print(f"[DataPreparer] ⚠️  在 {self.processed_dir} 中未找到处理后的图片")
            print("  请先运行 prepare() 处理原始图片")
            return []

        caption_paths = []
        for img_path in sorted(processed_images):
            caption_parts = [trigger_word]
            if description:
                caption_parts.append(description)

            caption_text = ", ".join(caption_parts)
            caption_path = img_path.with_suffix(".txt")
            caption_path.write_text(caption_text, encoding="utf-8")
            caption_paths.append(str(caption_path))

        print(
            f"[DataPreparer] 已为 {len(caption_paths)} 张图片生成 caption 文件\n"
            f"  触发词: {trigger_word}\n"
            f"  Caption 格式: \"{trigger_word}, {description or '...'}\"\n"
            "  ℹ️  后续版本将接入大模型进行智能描述（当前为模板占位）"
        )
        return caption_paths

    def verify(self) -> dict:
        """
        验证处理后的数据集是否准备就绪。

        检查项目：
        - 图片数量
        - 每张图片是否有对应的 caption 文件
        - 图片尺寸是否一致

        Returns:
            验证结果字典，包含 total、valid、missing_captions、size_issues 等字段。
        """
        if not self.processed_dir.exists():
            return {"error": f"目录不存在: {self.processed_dir}"}

        images = sorted(self.processed_dir.glob("*.png"))
        missing_captions = []
        size_issues = []
        sizes = set()

        for img_path in images:
            caption_path = img_path.with_suffix(".txt")
            if not caption_path.exists():
                missing_captions.append(img_path.name)

            try:
                with Image.open(img_path) as img:
                    sizes.add(img.size)
                    if len(sizes) > 1:
                        size_issues.append(f"{img_path.name}: {img.size}")
            except Exception as e:
                size_issues.append(f"{img_path.name}: 读取失败 ({e})")

        result = {
            "total": len(images),
            "valid": len(images) - len(missing_captions),
            "missing_captions": missing_captions,
            "size_issues": size_issues,
            "sizes": list(sizes),
        }

        print(f"[DataPreparer] 数据集验证结果:")
        print(f"  总图片数: {result['total']}")
        print(f"  有效图片（含caption）: {result['valid']}")
        if missing_captions:
            print(f"  ⚠️  缺少 caption 文件: {missing_captions}")
        if len(sizes) > 1:
            print(f"  ⚠️  尺寸不一致: {sizes}")
        else:
            print(f"  ✓ 尺寸统一: {list(sizes)[0] if sizes else '无图片'}")

        return result

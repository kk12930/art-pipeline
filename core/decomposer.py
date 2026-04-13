# core/decomposer.py
# UI 设计图自动拆解模块
# 使用 SAM（Segment Anything Model）自动分割图像，并按规则分类 UI 元素

import os
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import List, Optional

from PIL import Image

# 尝试导入 SAM 相关依赖，缺失时给出友好提示
try:
    import numpy as np
    _HAS_NUMPY = True
except ImportError:
    _HAS_NUMPY = False

try:
    import cv2
    _HAS_CV2 = True
except ImportError:
    _HAS_CV2 = False

try:
    from segment_anything import sam_model_registry, SamAutomaticMaskGenerator
    _HAS_SAM = True
except ImportError:
    _HAS_SAM = False


class ElementType(Enum):
    """UI 元素类型枚举"""
    BACKGROUND = auto()   # 背景（面积 > 50%）
    FRAME = auto()        # 底框/面板（宽扁形状，较大面积）
    BUTTON = auto()       # 按钮（中等面积，较规则矩形）
    BADGE = auto()        # 角标（小面积，位于角落）
    ICON = auto()         # 图标（小面积，近似正方形）
    DECORATION = auto()   # 装饰元素（其他形状）
    UNKNOWN = auto()      # 无法分类


@dataclass
class UIElement:
    """
    UI 元素数据类，存储分割结果和分类信息。

    Attributes:
        type: 元素类型（ElementType 枚举）。
        image: 该元素的裁剪图片（带透明通道的 RGBA）。
        bbox: 边界框 (x, y, width, height)，以像素为单位。
        area_ratio: 该元素占整体图片的面积比例（0.0~1.0）。
        confidence: 分类置信度（0.0~1.0，基于规则计算）。
    """
    type: ElementType
    image: Optional[Image.Image]
    bbox: tuple  # (x, y, w, h)
    area_ratio: float
    confidence: float = 1.0


class UIDecomposer:
    """
    UI 设计图自动拆解器。

    使用 SAM 模型自动分割图像中的各个元素，
    并基于面积比例、位置、宽高比等规则将元素分类为
    背景、底框、按钮、角标、图标或装饰元素。

    示例:
        decomposer = UIDecomposer(sam_checkpoint="models/sam/sam_vit_h_4b8939.pth")
        elements = decomposer.decompose("my_ui.png")
        decomposer.export_all(elements, "outputs/decomposed/")
    """

    def __init__(self, sam_checkpoint: str = None, model_type: str = "vit_h"):
        """
        初始化拆解器。

        Args:
            sam_checkpoint: SAM 模型权重文件路径。为 None 时需在调用 decompose 前设置。
            model_type: SAM 模型类型，支持 "vit_h"、"vit_l"、"vit_b"。
        """
        self.sam_checkpoint = sam_checkpoint
        self.model_type = model_type
        self._mask_generator = None

        # 检查依赖
        if not _HAS_NUMPY:
            print("[UIDecomposer] ⚠️  未安装 numpy，请运行：pip install numpy")
        if not _HAS_CV2:
            print("[UIDecomposer] ⚠️  未安装 opencv-python，请运行：pip install opencv-python")
        if not _HAS_SAM:
            print(
                "[UIDecomposer] ⚠️  未安装 segment-anything，请运行：\n"
                "  pip install git+https://github.com/facebookresearch/segment-anything.git\n"
                "  并下载模型权重：scripts/setup_models.py"
            )

    def _load_sam(self) -> None:
        """
        懒加载 SAM 模型（首次调用 decompose 时加载）。

        Raises:
            ImportError: 未安装 segment-anything 时抛出。
            FileNotFoundError: SAM 权重文件不存在时抛出。
        """
        if self._mask_generator is not None:
            return

        if not _HAS_SAM:
            raise ImportError(
                "请先安装 segment-anything：\n"
                "  pip install git+https://github.com/facebookresearch/segment-anything.git\n"
                "  并下载模型权重（运行 python scripts/setup_models.py 查看下载说明）"
            )
        if not _HAS_NUMPY:
            raise ImportError("请安装 numpy：pip install numpy")

        if not self.sam_checkpoint:
            raise ValueError("请提供 SAM 权重文件路径（sam_checkpoint 参数）")

        checkpoint_path = Path(self.sam_checkpoint)
        if not checkpoint_path.exists():
            raise FileNotFoundError(
                f"SAM 权重文件不存在: {checkpoint_path}\n"
                "请运行 python scripts/setup_models.py 查看下载说明"
            )

        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[UIDecomposer] 正在加载 SAM 模型 ({self.model_type}) 到 {device}...")

        sam = sam_model_registry[self.model_type](checkpoint=str(checkpoint_path))
        sam.to(device=device)

        # 自动掩码生成器参数（平衡速度与精度）
        self._mask_generator = SamAutomaticMaskGenerator(
            sam,
            points_per_side=32,           # 采样点密度
            pred_iou_thresh=0.86,         # IoU 阈值
            stability_score_thresh=0.92,  # 稳定性分数阈值
            min_mask_region_area=100,     # 最小分割区域（过滤噪点）
        )
        print("[UIDecomposer] SAM 模型加载完成 ✓")

    def _classify_element(
        self,
        mask: "np.ndarray",
        image_width: int,
        image_height: int,
    ) -> tuple[ElementType, float]:
        """
        根据规则对分割出的元素进行分类。

        分类规则：
        - 面积 > 50%  →  背景 (BACKGROUND)
        - 宽扁形状（宽/高 > 3）+ 中等面积  →  底框 (FRAME)
        - 小面积 + 角落位置  →  角标 (BADGE)
        - 小面积 + 近似正方形（宽高比 0.7~1.3）  →  图标 (ICON)
        - 中等面积 + 矩形  →  按钮 (BUTTON)
        - 其他  →  装饰 (DECORATION)

        Args:
            mask: 二值掩码数组（bool 类型，True 表示属于该元素）。
            image_width: 原始图片宽度。
            image_height: 原始图片高度。

        Returns:
            (ElementType, confidence) 元组。
        """
        import numpy as np

        total_area = image_width * image_height
        mask_area = int(np.sum(mask))
        area_ratio = mask_area / total_area

        # 获取边界框
        rows = np.any(mask, axis=1)
        cols = np.any(mask, axis=0)
        if not rows.any():
            return ElementType.UNKNOWN, 0.0

        y_min, y_max = np.where(rows)[0][[0, -1]]
        x_min, x_max = np.where(cols)[0][[0, -1]]
        bbox_w = int(x_max - x_min + 1)
        bbox_h = int(y_max - y_min + 1)
        aspect_ratio = bbox_w / bbox_h if bbox_h > 0 else 1.0

        # 判断是否在角落区域（距离任意边缘 < 15%）
        edge_threshold = 0.15
        near_left = x_min / image_width < edge_threshold
        near_right = (image_width - x_max) / image_width < edge_threshold
        near_top = y_min / image_height < edge_threshold
        near_bottom = (image_height - y_max) / image_height < edge_threshold
        in_corner = (near_left or near_right) and (near_top or near_bottom)

        # 分类规则
        if area_ratio > 0.5:
            return ElementType.BACKGROUND, 0.95

        if area_ratio < 0.05 and in_corner:
            return ElementType.BADGE, 0.85

        if area_ratio < 0.08 and 0.7 <= aspect_ratio <= 1.3:
            return ElementType.ICON, 0.80

        if aspect_ratio > 3.0 and 0.05 < area_ratio < 0.3:
            return ElementType.FRAME, 0.75

        if 0.05 < area_ratio < 0.2 and 1.5 <= aspect_ratio <= 5.0:
            return ElementType.BUTTON, 0.70

        return ElementType.DECORATION, 0.60

    def decompose(self, image_path: str) -> List[UIElement]:
        """
        对 UI 设计图进行自动分割和元素分类。

        Args:
            image_path: 输入图片路径（支持 PNG、JPG 等常见格式）。

        Returns:
            UIElement 列表，每个元素包含类型、裁剪图片、边界框等信息。
            按面积从大到小排序。

        Raises:
            FileNotFoundError: 图片文件不存在时抛出。
            ImportError: 缺少必要依赖（SAM、numpy、opencv）时抛出。
        """
        import numpy as np

        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"图片不存在: {image_path}")

        # 加载图片
        pil_image = Image.open(image_path).convert("RGBA")
        image_rgb = np.array(pil_image.convert("RGB"))
        h, w = image_rgb.shape[:2]

        # 懒加载 SAM 模型
        self._load_sam()

        print(f"[UIDecomposer] 正在分割: {image_path.name} ({w}x{h})")
        masks = self._mask_generator.generate(image_rgb)
        print(f"[UIDecomposer] 共检测到 {len(masks)} 个分割区域")

        elements = []
        for mask_data in masks:
            mask = mask_data["segmentation"]  # bool numpy array
            bbox_xywh = mask_data["bbox"]     # [x, y, w, h]
            area_ratio = mask_data["area"] / (w * h)

            # 分类
            elem_type, confidence = self._classify_element(mask, w, h)

            # 裁剪出带透明通道的元素图片
            elem_image = self._crop_element(pil_image, mask, bbox_xywh)

            elements.append(UIElement(
                type=elem_type,
                image=elem_image,
                bbox=tuple(bbox_xywh),
                area_ratio=area_ratio,
                confidence=confidence,
            ))

        # 按面积从大到小排序
        elements.sort(key=lambda e: e.area_ratio, reverse=True)
        print(
            f"[UIDecomposer] 分类结果: "
            + ", ".join(
                f"{t.name}×{sum(1 for e in elements if e.type == t)}"
                for t in ElementType
                if any(e.type == t for e in elements)
            )
        )
        return elements

    def _crop_element(
        self,
        image: Image.Image,
        mask: "np.ndarray",
        bbox: list,
    ) -> Image.Image:
        """
        按掩码裁剪元素，生成带透明通道（Alpha）的 PNG 图片。

        Args:
            image: 原始 RGBA 图片。
            mask: 元素的二值掩码（bool numpy array）。
            bbox: 边界框 [x, y, w, h]。

        Returns:
            裁剪后的 RGBA PIL.Image 对象。
        """
        import numpy as np

        x, y, bw, bh = [int(v) for v in bbox]
        img_array = np.array(image)

        # 将掩码外的像素设为透明
        result = img_array.copy()
        result[~mask, 3] = 0  # alpha 通道置 0

        # 裁剪到边界框
        cropped = result[y:y + bh, x:x + bw]
        return Image.fromarray(cropped, "RGBA")

    def export_all(self, elements: List[UIElement], output_dir: str) -> List[str]:
        """
        批量导出所有 UI 元素为带透明通道的 PNG 文件。

        文件名格式：{index:02d}_{element_type}_{area_ratio:.2f}.png
        例如：00_BACKGROUND_0.62.png、01_FRAME_0.18.png

        Args:
            elements: UIElement 列表（通常来自 decompose() 的返回值）。
            output_dir: 输出目录路径，不存在时自动创建。

        Returns:
            所有导出文件的路径列表。
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        exported_paths = []
        for idx, element in enumerate(elements):
            if element.image is None:
                continue

            # 确保使用 RGBA 模式（带透明通道）
            img = element.image
            if img.mode != "RGBA":
                img = img.convert("RGBA")

            filename = f"{idx:02d}_{element.type.name}_{element.area_ratio:.2f}.png"
            file_path = output_path / filename
            img.save(str(file_path), "PNG")
            exported_paths.append(str(file_path))
            print(f"[UIDecomposer] 已导出: {filename}")

        print(f"[UIDecomposer] 共导出 {len(exported_paths)} 个元素到 {output_dir}")
        return exported_paths

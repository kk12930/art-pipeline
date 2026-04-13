"""
UI 设计图自动拆解模块
使用 SAM（Segment Anything Model）自动分割图像元素，并按规则分类
"""

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional, Tuple

from PIL import Image

# 尝试导入 SAM 相关依赖，缺失时给出友好提示而非直接崩溃
try:
    import numpy as np
    _NUMPY_AVAILABLE = True
except ImportError:
    _NUMPY_AVAILABLE = False
    print("[警告] numpy 未安装，UI 拆解功能不可用。请运行: pip install numpy")

try:
    from segment_anything import SamAutomaticMaskGenerator, sam_model_registry
    _SAM_AVAILABLE = True
except ImportError:
    _SAM_AVAILABLE = False
    print(
        "[警告] segment-anything 未安装，UI 拆解功能不可用。\n"
        "  安装方式: pip install git+https://github.com/facebookresearch/segment-anything.git"
    )

try:
    import cv2
    _CV2_AVAILABLE = True
except ImportError:
    _CV2_AVAILABLE = False
    print("[警告] opencv-python 未安装，UI 拆解功能不可用。请运行: pip install opencv-python")


class ElementType(Enum):
    """UI 元素分类枚举"""
    BACKGROUND = "background"    # 背景
    FRAME = "frame"              # 底框/面板
    BUTTON = "button"            # 按钮
    BADGE = "badge"              # 角标/徽章
    ICON = "icon"                # 图标
    DECORATION = "decoration"    # 装饰元素
    UNKNOWN = "unknown"          # 未知


@dataclass
class UIElement:
    """
    UI 元素数据类
    存储分割结果和分类信息
    """
    type: ElementType                      # 元素类型
    image: Image.Image                     # 裁剪出的元素图片（带透明通道）
    bbox: Tuple[int, int, int, int]        # 边界框 (x, y, w, h)
    area_ratio: float                      # 占整图面积的比例 0.0~1.0
    confidence: float = 1.0               # 分类置信度


def _check_dependencies() -> bool:
    """检查运行 UIDecomposer 所需的全部依赖是否已安装"""
    missing = []
    if not _NUMPY_AVAILABLE:
        missing.append("numpy")
    if not _SAM_AVAILABLE:
        missing.append(
            "segment-anything (pip install git+https://github.com/facebookresearch/segment-anything.git)"
        )
    if not _CV2_AVAILABLE:
        missing.append("opencv-python")
    if missing:
        print("[错误] 缺少以下依赖，请先安装：")
        for pkg in missing:
            print(f"  - {pkg}")
        return False
    return True


class UIDecomposer:
    """
    UI 设计图自动拆解器
    使用 SAM 自动分割 + 规则分类，将整张 UI 图拆解为各个元素
    """

    def __init__(self, sam_checkpoint: str = "models/sam/sam_vit_h.pth", model_type: str = "vit_h"):
        """
        初始化 UIDecomposer

        Args:
            sam_checkpoint: SAM 模型权重路径
            model_type:     SAM 模型类型，支持 "vit_h"、"vit_l"、"vit_b"
        """
        self.sam_checkpoint = sam_checkpoint
        self.model_type = model_type
        self._mask_generator = None

    def _load_sam(self) -> None:
        """内部方法：加载 SAM 模型（懒加载，首次使用时才加载）"""
        if not _check_dependencies():
            raise ImportError("缺少必要依赖，请参考上方提示安装")

        checkpoint = Path(self.sam_checkpoint)
        if not checkpoint.exists():
            raise FileNotFoundError(
                f"SAM 模型文件不存在: {checkpoint}\n"
                "请运行 python scripts/setup_models.py 查看下载指引"
            )

        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[信息] 正在加载 SAM 模型 ({self.model_type})，设备: {device}")
        sam = sam_model_registry[self.model_type](checkpoint=str(checkpoint))
        sam.to(device=device)
        self._mask_generator = SamAutomaticMaskGenerator(
            model=sam,
            points_per_side=32,          # 采样点密度
            pred_iou_thresh=0.88,        # IoU 阈值
            stability_score_thresh=0.95, # 稳定性阈值
        )
        print("[信息] SAM 模型加载完成")

    def _classify_element(
        self,
        bbox: Tuple[int, int, int, int],
        area_ratio: float,
        img_width: int,
        img_height: int,
    ) -> Tuple[ElementType, float]:
        """
        按规则对元素进行分类

        分类规则：
          - 面积 > 50%  → 背景（BACKGROUND）
          - 面积 > 20%  → 底框（FRAME）
          - 小面积 + 角落位置 → 角标（BADGE）
          - 正方形 + 小面积（<5%）→ 图标（ICON）
          - 宽扁形状（宽/高 > 2.5）→ 底框（FRAME）或按钮（BUTTON）
          - 其他 → 装饰（DECORATION）

        Args:
            bbox:       (x, y, w, h)
            area_ratio: 占图面积比例
            img_width:  原图宽度
            img_height: 原图高度

        Returns:
            (ElementType, confidence)
        """
        x, y, w, h = bbox
        aspect_ratio = w / h if h > 0 else 1.0

        # 判断是否在角落位置（距边缘 < 15% 的区域）
        margin_x = 0.15 * img_width
        margin_y = 0.15 * img_height
        in_corner = (
            (x < margin_x or x + w > img_width - margin_x)
            and (y < margin_y or y + h > img_height - margin_y)
        )

        if area_ratio > 0.5:
            return ElementType.BACKGROUND, 0.95
        if area_ratio > 0.2:
            return ElementType.FRAME, 0.85
        if area_ratio < 0.03 and in_corner:
            return ElementType.BADGE, 0.80
        if 0.8 < aspect_ratio < 1.2 and area_ratio < 0.05:
            return ElementType.ICON, 0.82
        if aspect_ratio > 2.5:
            # 宽扁且面积较大 → 底框，否则 → 按钮
            return (ElementType.FRAME if area_ratio > 0.05 else ElementType.BUTTON), 0.75
        return ElementType.DECORATION, 0.60

    def decompose(self, image_path: str) -> List[UIElement]:
        """
        对输入图片进行自动分割和元素分类

        Args:
            image_path: 输入图片路径

        Returns:
            UIElement 列表，按面积从大到小排序
        """
        if self._mask_generator is None:
            self._load_sam()

        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"图片文件不存在: {image_path}")

        print(f"[信息] 正在拆解图片: {image_path}")
        pil_image = Image.open(image_path).convert("RGBA")
        img_width, img_height = pil_image.size
        total_area = img_width * img_height

        # SAM 需要 RGB numpy 数组输入
        rgb_array = np.array(pil_image.convert("RGB"))
        masks = self._mask_generator.generate(rgb_array)
        print(f"[信息] SAM 共检测到 {len(masks)} 个区域")

        elements: List[UIElement] = []
        rgba_array = np.array(pil_image)

        for mask_data in masks:
            mask = mask_data["segmentation"]            # bool 数组 (H, W)
            x, y, w, h = mask_data["bbox"]             # xywh 格式
            area_ratio = mask_data["area"] / total_area

            # 裁剪元素区域，保留透明通道
            cropped = rgba_array[y : y + h, x : x + w].copy()
            # 将 mask 以外的像素设为透明
            mask_crop = mask[y : y + h, x : x + w]
            cropped[~mask_crop, 3] = 0
            element_image = Image.fromarray(cropped, "RGBA")

            elem_type, confidence = self._classify_element(
                (x, y, w, h), area_ratio, img_width, img_height
            )
            elements.append(
                UIElement(
                    type=elem_type,
                    image=element_image,
                    bbox=(x, y, w, h),
                    area_ratio=area_ratio,
                    confidence=confidence,
                )
            )

        # 按面积从大到小排序
        elements.sort(key=lambda e: e.area_ratio, reverse=True)
        print(f"[信息] 拆解完成，共 {len(elements)} 个元素")
        return elements

    def export_all(self, elements: List[UIElement], output_dir: str) -> List[str]:
        """
        批量导出所有元素为带透明通道的 PNG 文件

        Args:
            elements:   UIElement 列表（由 decompose() 返回）
            output_dir: 输出目录路径

        Returns:
            导出的文件路径列表
        """
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        saved_paths: List[str] = []
        # 按类型分组计数，生成有意义的文件名
        type_counters: dict = {}
        for elem in elements:
            type_name = elem.type.value
            idx = type_counters.get(type_name, 0)
            type_counters[type_name] = idx + 1
            filename = f"{type_name}_{idx:02d}.png"
            out_path = out_dir / filename
            elem.image.save(str(out_path), "PNG")
            saved_paths.append(str(out_path))
            print(f"[信息] 已导出: {out_path}")

        print(f"[信息] 共导出 {len(saved_paths)} 个元素到 {out_dir}")
        return saved_paths

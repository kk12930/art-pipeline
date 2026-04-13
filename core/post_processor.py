"""
后处理引擎
提供超分辨率放大、Icon 标准化和批量多尺寸导出功能
"""

import os
from pathlib import Path
from typing import List, Tuple

from PIL import Image, ImageOps

# 尝试导入 Real-ESRGAN，缺失时给出友好提示而非直接崩溃
try:
    from basicsr.archs.rrdbnet_arch import RRDBNet
    from realesrgan import RealESRGANer
    _REALESRGAN_AVAILABLE = True
except ImportError:
    _REALESRGAN_AVAILABLE = False
    print(
        "[警告] realesrgan/basicsr 未安装，超分辨率功能不可用。\n"
        "  安装方式: pip install realesrgan basicsr"
    )


class PostProcessor:
    """
    后处理引擎
    支持 Real-ESRGAN 超分、Icon 标准化（居中+padding）和批量多尺寸导出
    """

    def __init__(self, realesrgan_model_path: str = ""):
        """
        初始化后处理引擎

        Args:
            realesrgan_model_path: Real-ESRGAN 模型权重路径（可选）
        """
        self.realesrgan_model_path = realesrgan_model_path
        self._upsampler = None

    def _load_realesrgan(self) -> None:
        """内部方法：懒加载 Real-ESRGAN 超分模型"""
        if not _REALESRGAN_AVAILABLE:
            raise ImportError(
                "请先安装 realesrgan: pip install realesrgan basicsr"
            )

        import torch
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # 使用 RRDBNet x4 架构（Real-ESRGAN 默认配置）
        model = RRDBNet(
            num_in_ch=3, num_out_ch=3, num_feat=64,
            num_block=23, num_grow_ch=32, scale=4,
        )
        self._upsampler = RealESRGANer(
            scale=4,
            model_path=self.realesrgan_model_path or "",
            model=model,
            tile=0,          # 0 表示不分块处理（显存足够时）
            tile_pad=10,
            pre_pad=0,
            half=True,       # fp16 节省显存
            device=device,
        )
        print("[信息] Real-ESRGAN 模型加载完成")

    def upscale(self, image: Image.Image, scale: int = 4) -> Image.Image:
        """
        使用 Real-ESRGAN 对图片进行超分辨率放大

        Args:
            image: 输入 PIL 图片
            scale: 放大倍数，默认 4

        Returns:
            放大后的 PIL 图片

        Raises:
            ImportError: 未安装 realesrgan
        """
        if not _REALESRGAN_AVAILABLE:
            print("[警告] Real-ESRGAN 不可用，使用 Lanczos 降级超分")
            w, h = image.size
            return image.resize((w * scale, h * scale), Image.Resampling.LANCZOS)

        if self._upsampler is None:
            self._load_realesrgan()

        import numpy as np
        # Real-ESRGAN 需要 numpy BGR 输入
        img_array = np.array(image.convert("RGB"))
        img_bgr = img_array[:, :, ::-1]  # RGB → BGR

        output, _ = self._upsampler.enhance(img_bgr, outscale=scale)
        # BGR → RGB → PIL
        output_rgb = output[:, :, ::-1]
        return Image.fromarray(output_rgb)

    def standardize_icon(
        self,
        image: Image.Image,
        target_size: int = 128,
        padding: int = 8,
    ) -> Image.Image:
        """
        标准化 Icon：将图片居中缩放并加 padding，统一为正方形尺寸

        Args:
            image:       输入 PIL 图片（建议带透明通道）
            target_size: 输出正方形的边长（像素），默认 128
            padding:     四边留白像素数，默认 8

        Returns:
            标准化后的 RGBA 图片，尺寸为 target_size x target_size
        """
        # 转换为 RGBA 以支持透明背景
        image = image.convert("RGBA")

        # 计算内容区域大小（减去 padding）
        content_size = target_size - 2 * padding
        if content_size <= 0:
            raise ValueError(f"padding({padding}) 过大，超出 target_size({target_size})")

        # 等比缩放，使图片适应内容区域
        image.thumbnail((content_size, content_size), Image.Resampling.LANCZOS)
        thumb_w, thumb_h = image.size

        # 创建透明背景画布
        canvas = Image.new("RGBA", (target_size, target_size), (0, 0, 0, 0))

        # 将缩放后的图片居中粘贴
        offset_x = (target_size - thumb_w) // 2
        offset_y = (target_size - thumb_h) // 2
        canvas.paste(image, (offset_x, offset_y), mask=image)

        return canvas

    def batch_export(
        self,
        image: Image.Image,
        sizes: List[Tuple[int, int]],
        output_dir: str,
        filename_prefix: str = "export",
    ) -> List[str]:
        """
        批量多尺寸导出图片

        Args:
            image:           源 PIL 图片
            sizes:           目标尺寸列表，每项为 (width, height)
            output_dir:      输出目录路径
            filename_prefix: 文件名前缀，默认 "export"

        Returns:
            导出的文件路径列表
        """
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        saved_paths: List[str] = []
        for width, height in sizes:
            resized = image.resize((width, height), Image.Resampling.LANCZOS)
            filename = f"{filename_prefix}_{width}x{height}.png"
            out_path = out_dir / filename
            resized.save(str(out_path), "PNG")
            saved_paths.append(str(out_path))
            print(f"[信息] 已导出: {out_path}")

        print(f"[信息] 批量导出完成，共 {len(saved_paths)} 个文件")
        return saved_paths

# core/post_processor.py
# 后处理引擎
# 提供超分辨率、图标标准化、批量多尺寸导出等功能

import os
from pathlib import Path
from typing import List, Tuple

from PIL import Image, ImageFilter

# 尝试导入 Real-ESRGAN，缺失时给出友好提示
try:
    from realesrgan import RealESRGANer
    from basicsr.archs.rrdbnet_arch import RRDBNet
    _HAS_REALESRGAN = True
except ImportError:
    _HAS_REALESRGAN = False


class PostProcessor:
    """
    后处理引擎，提供图片质量优化和标准化导出功能。

    主要功能：
    - upscale: Real-ESRGAN 超分辨率放大
    - standardize_icon: 图标标准化（居中 + padding + 统一尺寸）
    - batch_export: 批量多尺寸导出

    Real-ESRGAN 为可选依赖，未安装时 upscale 方法会退回到 PIL 双线性插值。
    安装方法：pip install realesrgan
    """

    def __init__(self, esrgan_model_path: str = None):
        """
        初始化后处理引擎。

        Args:
            esrgan_model_path: Real-ESRGAN 模型权重路径。
                               为 None 时使用 PIL 插值作为备用方案。
        """
        self.esrgan_model_path = esrgan_model_path
        self._upsampler = None

        if not _HAS_REALESRGAN:
            print(
                "[PostProcessor] ℹ️  未安装 realesrgan，upscale 将使用 PIL 双线性插值作为替代。\n"
                "  如需 Real-ESRGAN 超分辨率，请运行：pip install realesrgan"
            )

    def _load_esrgan(self) -> None:
        """
        懒加载 Real-ESRGAN 模型（首次调用 upscale 时加载）。

        Raises:
            ImportError: 未安装 realesrgan 时抛出。
            FileNotFoundError: 模型权重文件不存在时抛出。
        """
        if self._upsampler is not None:
            return

        if not _HAS_REALESRGAN:
            raise ImportError(
                "请安装 Real-ESRGAN：pip install realesrgan\n"
                "并下载模型权重（运行 python scripts/setup_models.py 查看说明）"
            )

        if not self.esrgan_model_path:
            raise ValueError("请提供 Real-ESRGAN 模型权重路径（esrgan_model_path 参数）")

        model_path = Path(self.esrgan_model_path)
        if not model_path.exists():
            raise FileNotFoundError(
                f"Real-ESRGAN 权重文件不存在: {model_path}\n"
                "请运行 python scripts/setup_models.py 查看下载说明"
            )

        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[PostProcessor] 正在加载 Real-ESRGAN 模型到 {device}...")

        # 使用 RealESRGAN x4plus 架构
        model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64,
                        num_block=23, num_grow_ch=32, scale=4)
        self._upsampler = RealESRGANer(
            scale=4,
            model_path=str(model_path),
            model=model,
            tile=512,         # 分块处理，适配 16G 显存
            tile_pad=10,
            pre_pad=0,
            half=True,        # fp16 节省显存
            device=device,
        )
        print("[PostProcessor] Real-ESRGAN 加载完成 ✓")

    def upscale(self, image: Image.Image, scale: int = 4) -> Image.Image:
        """
        对图片进行超分辨率放大。

        优先使用 Real-ESRGAN（如已安装），否则退回到 PIL 高质量插值。

        Args:
            image: 输入 PIL 图片（支持 RGB、RGBA）。
            scale: 放大倍数，Real-ESRGAN 固定为 4x；PIL 模式支持任意整数。

        Returns:
            放大后的 PIL.Image 对象。
        """
        if _HAS_REALESRGAN and self.esrgan_model_path:
            return self._upscale_esrgan(image)
        else:
            return self._upscale_pil(image, scale)

    def _upscale_esrgan(self, image: Image.Image) -> Image.Image:
        """使用 Real-ESRGAN 进行超分辨率（内部方法）"""
        import numpy as np

        self._load_esrgan()

        # 保存 alpha 通道（RGBA 图片）
        has_alpha = image.mode == "RGBA"
        if has_alpha:
            alpha = image.split()[3]
            image_rgb = image.convert("RGB")
        else:
            image_rgb = image

        # Real-ESRGAN 需要 numpy BGR 格式
        img_array = np.array(image_rgb)[:, :, ::-1]  # RGB → BGR
        output, _ = self._upsampler.enhance(img_array, outscale=4)
        output_rgb = output[:, :, ::-1]  # BGR → RGB
        result = Image.fromarray(output_rgb, "RGB")

        # 恢复 alpha 通道
        if has_alpha:
            new_w, new_h = result.size
            alpha_resized = alpha.resize((new_w, new_h), Image.LANCZOS)
            result = result.convert("RGBA")
            result.putalpha(alpha_resized)

        return result

    def _upscale_pil(self, image: Image.Image, scale: int) -> Image.Image:
        """使用 PIL LANCZOS 插值进行放大（Real-ESRGAN 的备用方案）"""
        w, h = image.size
        new_size = (w * scale, h * scale)
        print(f"[PostProcessor] 使用 PIL LANCZOS 插值放大 {scale}x: {w}x{h} → {new_size[0]}x{new_size[1]}")
        return image.resize(new_size, Image.LANCZOS)

    def standardize_icon(
        self,
        image: Image.Image,
        target_size: int = 256,
        padding: int = 16,
    ) -> Image.Image:
        """
        标准化图标：将图标居中放置在统一尺寸的画布上，并添加内边距。

        处理流程：
        1. 将图片转换为 RGBA（保留透明通道）
        2. 计算内容区域（去除透明边缘）
        3. 缩放到 target_size - padding*2 的尺寸（等比缩放）
        4. 居中放置在 target_size x target_size 的透明画布上

        Args:
            image: 输入图标图片（建议为带透明通道的 PNG）。
            target_size: 目标画布尺寸（正方形），单位像素。默认 256。
            padding: 内边距，单位像素。默认 16（每边 16 像素留白）。

        Returns:
            标准化后的正方形 RGBA 图片。
        """
        # 确保是 RGBA 模式
        if image.mode != "RGBA":
            image = image.convert("RGBA")

        # 裁剪透明边缘（获取实际内容边界框）
        bbox = image.getbbox()
        if bbox:
            image = image.crop(bbox)

        # 计算缩放后的尺寸（保持宽高比）
        content_size = target_size - padding * 2
        w, h = image.size
        if w == 0 or h == 0:
            return Image.new("RGBA", (target_size, target_size), (0, 0, 0, 0))

        scale_ratio = min(content_size / w, content_size / h)
        new_w = int(w * scale_ratio)
        new_h = int(h * scale_ratio)
        resized = image.resize((new_w, new_h), Image.LANCZOS)

        # 创建透明背景画布，将图标居中粘贴
        canvas = Image.new("RGBA", (target_size, target_size), (0, 0, 0, 0))
        paste_x = (target_size - new_w) // 2
        paste_y = (target_size - new_h) // 2
        canvas.paste(resized, (paste_x, paste_y), resized)

        return canvas

    def batch_export(
        self,
        image: Image.Image,
        sizes: List[int],
        output_dir: str,
        base_name: str = "icon",
        format: str = "PNG",
    ) -> List[str]:
        """
        批量多尺寸导出图片。

        对每个指定尺寸，先调用 standardize_icon 标准化，
        再保存为对应分辨率的文件。

        Args:
            image: 输入图片（通常为生成的图标）。
            sizes: 导出尺寸列表（正方形），如 [64, 128, 256, 512]。
            output_dir: 输出目录路径，不存在时自动创建。
            base_name: 输出文件名前缀，默认为 "icon"。
            format: 输出格式，默认 "PNG"（支持透明通道）。

        Returns:
            所有导出文件的路径列表。

        Example:
            >>> processor = PostProcessor()
            >>> paths = processor.batch_export(img, [64, 128, 256], "outputs/icons/")
            >>> # 生成: icon_64x64.png, icon_128x128.png, icon_256x256.png
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        exported_paths = []
        for size in sizes:
            standardized = self.standardize_icon(image, target_size=size)
            ext = format.lower()
            filename = f"{base_name}_{size}x{size}.{ext}"
            file_path = output_path / filename
            standardized.save(str(file_path), format)
            exported_paths.append(str(file_path))
            print(f"[PostProcessor] 已导出: {filename}")

        print(f"[PostProcessor] 批量导出完成，共 {len(exported_paths)} 个文件")
        return exported_paths

    def remove_background(self, image: Image.Image, threshold: int = 10) -> Image.Image:
        """
        简单的背景去除（基于边角颜色采样）。

        注意：这是一个简化实现，对复杂背景效果有限。
        生产环境建议使用 rembg 库（pip install rembg）。

        Args:
            image: 输入 RGB/RGBA 图片。
            threshold: 颜色匹配容差（0~255），越大匹配范围越宽。

        Returns:
            背景透明的 RGBA 图片。
        """
        rgba = image.convert("RGBA")
        data = rgba.getdata()

        # 取左上角像素作为背景色
        bg_color = data[0][:3]

        new_data = []
        for pixel in data:
            r, g, b, a = pixel
            # 判断是否与背景色接近
            if (
                abs(r - bg_color[0]) <= threshold
                and abs(g - bg_color[1]) <= threshold
                and abs(b - bg_color[2]) <= threshold
            ):
                new_data.append((r, g, b, 0))  # 透明
            else:
                new_data.append(pixel)

        rgba.putdata(new_data)
        return rgba

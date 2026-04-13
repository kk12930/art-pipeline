"""
图片生成核心引擎
封装 SDXL + LoRA 推理，针对 16G 显存做内存优化
"""

import os
import torch
from pathlib import Path
from typing import Optional

# 延迟导入，避免在未安装依赖时报错
try:
    from diffusers import StableDiffusionXLPipeline
    _DIFFUSERS_AVAILABLE = True
except ImportError:
    _DIFFUSERS_AVAILABLE = False
    print("[警告] diffusers 未安装，图片生成功能不可用。请运行: pip install diffusers")

from PIL import Image


class ArtGenerator:
    """
    美术资源生成器
    封装 SDXL 基础模型 + LoRA 推理，支持 16G 显存优化配置
    """

    def __init__(self, model_config: dict):
        """
        初始化生成器

        Args:
            model_config: 模型配置字典，通常从 configs/model_config.yaml 加载
        """
        self.config = model_config
        self.pipeline = None
        self.device = model_config.get("device", "cuda")
        # 根据配置选择数据类型
        dtype_str = model_config.get("dtype", "float16")
        self.torch_dtype = torch.float16 if dtype_str == "float16" else torch.float32

    def load_model(self) -> None:
        """
        加载 SDXL 基础模型
        针对 16G 显存启用 cpu_offload 和 vae_tiling 以节省显存
        """
        if not _DIFFUSERS_AVAILABLE:
            raise ImportError("请先安装 diffusers: pip install diffusers>=0.27.0")

        base_model = self.config.get("base_model", "stabilityai/stable-diffusion-xl-base-1.0")
        print(f"[信息] 正在加载基础模型: {base_model}")

        self.pipeline = StableDiffusionXLPipeline.from_pretrained(
            base_model,
            torch_dtype=self.torch_dtype,
            use_safetensors=True,
            variant="fp16",
        )

        # 启用 CPU offload，将不活跃的模型组件卸载到 CPU，节省显存
        if self.config.get("enable_cpu_offload", True):
            print("[信息] 启用 model_cpu_offload（节省显存）")
            self.pipeline.enable_model_cpu_offload()
        else:
            self.pipeline = self.pipeline.to(self.device)

        # 启用 VAE tiling，处理高分辨率图像时减少显存占用
        if self.config.get("enable_vae_tiling", True):
            print("[信息] 启用 vae_tiling（支持高分辨率生成）")
            self.pipeline.enable_vae_tiling()

        print("[信息] 模型加载完成")

    def load_lora(self, lora_path: str, weight: float = 0.8) -> None:
        """
        加载自定义 LoRA 权重

        Args:
            lora_path: LoRA 权重文件路径（.safetensors 或 .pt）
            weight:    LoRA 强度，范围 0.0 ~ 1.0，默认 0.8
        """
        if self.pipeline is None:
            raise RuntimeError("请先调用 load_model() 加载基础模型")

        lora_path = Path(lora_path)
        if not lora_path.exists():
            raise FileNotFoundError(f"LoRA 文件不存在: {lora_path}")

        print(f"[信息] 正在加载 LoRA: {lora_path}，权重强度: {weight}")
        self.pipeline.load_lora_weights(str(lora_path.parent), weight_name=lora_path.name)
        # 融合 LoRA 权重到模型中，提升推理速度
        self.pipeline.fuse_lora(lora_scale=weight)
        print("[信息] LoRA 加载完成")

    def generate(
        self,
        prompt: str,
        negative_prompt: str = "",
        width: int = 1024,
        height: int = 1024,
        steps: int = 30,
        guidance_scale: float = 7.5,
        seed: Optional[int] = None,
    ) -> Image.Image:
        """
        生成图片

        Args:
            prompt:          正面提示词
            negative_prompt: 负面提示词
            width:           图片宽度（像素）
            height:          图片高度（像素）
            steps:           推理步数，越高质量越好但越慢
            guidance_scale:  CFG 引导强度
            seed:            随机种子，None 表示随机

        Returns:
            PIL.Image.Image 生成的图片对象
        """
        if self.pipeline is None:
            raise RuntimeError("请先调用 load_model() 加载基础模型")

        # 设置随机种子（可复现）
        generator = None
        if seed is not None:
            generator = torch.Generator(device="cpu").manual_seed(seed)
            print(f"[信息] 使用随机种子: {seed}")

        print(f"[信息] 开始生成图片，尺寸: {width}x{height}，步数: {steps}")

        result = self.pipeline(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            num_inference_steps=steps,
            guidance_scale=guidance_scale,
            generator=generator,
        )

        image = result.images[0]
        print("[信息] 图片生成完成")
        return image

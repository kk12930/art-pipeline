# core/generator.py
# 图片生成核心引擎
# 封装 SDXL + LoRA 推理逻辑，适配 16G 显存的内存优化配置

import os
from pathlib import Path
from PIL import Image


class ArtGenerator:
    """
    SDXL + LoRA 图片生成核心引擎。

    适配本地 RTX 5060 Ti 16G 显存，启用以下优化：
    - fp16 半精度推理
    - model_cpu_offload（将不活跃组件卸载到 CPU）
    - vae_tiling（大图生成分块处理）
    - attention_slicing（进一步节省显存）
    """

    def __init__(self, model_config: dict = None):
        """
        初始化生成器。

        Args:
            model_config: 模型配置字典，通常从 configs/model_config.yaml 加载。
                          为 None 时使用默认配置。
        """
        self.pipe = None
        self.config = model_config or {}
        self._base_model = self.config.get(
            "base_model", "stabilityai/stable-diffusion-xl-base-1.0"
        )
        self._vae_model = self.config.get("vae_model", "madebyollin/sdxl-vae-fp16-fix")
        self._mem_opt = self.config.get("memory_optimization", {})

    def load_model(self) -> None:
        """
        加载 SDXL 基础模型并应用显存优化。

        会自动启用以下优化（适配 16G 显卡）：
        - fp16 推理
        - model_cpu_offload（不活跃组件卸载到 CPU）
        - vae_tiling（分块处理大图）
        - attention_slicing（注意力分片）

        Raises:
            ImportError: 未安装 diffusers 或 transformers 时抛出。
            RuntimeError: 模型加载失败时抛出。
        """
        try:
            from diffusers import StableDiffusionXLPipeline, AutoencoderKL
        except ImportError:
            raise ImportError(
                "请安装 diffusers：pip install diffusers>=0.27.0 transformers>=4.38.0"
            )

        import torch
        use_fp16 = self._mem_opt.get("use_fp16", True)
        dtype = torch.float16 if use_fp16 else torch.float32

        print(f"[ArtGenerator] 正在加载基础模型: {self._base_model}")

        # 加载专用 VAE（提升图片质量，fp16 版本减少显存占用）
        vae = None
        if self._vae_model:
            print(f"[ArtGenerator] 正在加载 VAE: {self._vae_model}")
            vae = AutoencoderKL.from_pretrained(self._vae_model, torch_dtype=dtype)

        # 加载 SDXL pipeline
        kwargs = {"torch_dtype": dtype, "use_safetensors": True}
        if vae is not None:
            kwargs["vae"] = vae

        self.pipe = StableDiffusionXLPipeline.from_pretrained(
            self._base_model, **kwargs
        )

        # 显存优化：CPU 卸载
        enable_cpu_offload = self._mem_opt.get("enable_cpu_offload", True)
        if enable_cpu_offload:
            self.pipe.enable_model_cpu_offload()
            print("[ArtGenerator] 已启用 model_cpu_offload")

        # 显存优化：VAE tiling（大图生成时分块处理）
        enable_vae_tiling = self._mem_opt.get("enable_vae_tiling", True)
        if enable_vae_tiling:
            self.pipe.enable_vae_tiling()
            print("[ArtGenerator] 已启用 VAE tiling")

        # 显存优化：attention slicing
        enable_attention_slicing = self._mem_opt.get("enable_attention_slicing", True)
        if enable_attention_slicing:
            self.pipe.enable_attention_slicing()
            print("[ArtGenerator] 已启用 attention slicing")

        print("[ArtGenerator] 模型加载完成 ✓")

    def load_lora(self, lora_path: str, weight: float = 0.8) -> None:
        """
        加载自定义 LoRA 权重。

        Args:
            lora_path: LoRA 权重文件路径（.safetensors 或 .pt 格式）。
            weight: LoRA 权重系数，范围 0.0~1.0，越大风格越明显。默认 0.8。

        Raises:
            FileNotFoundError: LoRA 文件不存在时抛出。
            RuntimeError: 模型未加载时抛出。
        """
        if self.pipe is None:
            raise RuntimeError("请先调用 load_model() 加载基础模型")

        lora_path = Path(lora_path)
        if not lora_path.exists():
            raise FileNotFoundError(f"LoRA 文件不存在: {lora_path}")

        print(f"[ArtGenerator] 正在加载 LoRA: {lora_path} (weight={weight})")
        self.pipe.load_lora_weights(str(lora_path.parent), weight_name=lora_path.name)
        self.pipe.fuse_lora(lora_scale=weight)
        print(f"[ArtGenerator] LoRA 加载完成 ✓ (scale={weight})")

    def generate(
        self,
        prompt: str,
        negative_prompt: str = "",
        width: int = 1024,
        height: int = 1024,
        steps: int = 30,
        guidance_scale: float = 7.5,
        seed: int = None,
    ) -> Image.Image:
        """
        生成一张图片。

        Args:
            prompt: 正面提示词。
            negative_prompt: 负面提示词，描述不希望出现的内容。
            width: 生成图片宽度（像素）。建议使用 1024 的倍数。
            height: 生成图片高度（像素）。建议使用 1024 的倍数。
            steps: 去噪步数，越多质量越高但越慢。推荐 20~50。
            guidance_scale: 提示词引导强度，越高越贴近提示词但可能过饱和。推荐 7.0~9.0。
            seed: 随机种子，设置后可复现相同结果。为 None 则随机。

        Returns:
            PIL.Image.Image: 生成的图片对象。

        Raises:
            RuntimeError: 模型未加载时抛出。
        """
        if self.pipe is None:
            raise RuntimeError("请先调用 load_model() 加载基础模型")

        # 设置随机种子（确保可复现）
        import torch
        generator = None
        if seed is not None:
            generator = torch.Generator(device="cpu").manual_seed(seed)

        print(
            f"[ArtGenerator] 开始生成 | {width}x{height} | steps={steps} | "
            f"cfg={guidance_scale} | seed={seed}"
        )
        print(f"[ArtGenerator] prompt: {prompt[:80]}...")

        result = self.pipe(
            prompt=prompt,
            negative_prompt=negative_prompt if negative_prompt else None,
            width=width,
            height=height,
            num_inference_steps=steps,
            guidance_scale=guidance_scale,
            generator=generator,
        )

        image = result.images[0]
        print("[ArtGenerator] 生成完成 ✓")
        return image

    def unload_lora(self) -> None:
        """
        卸载当前加载的 LoRA 权重，恢复到基础模型状态。
        """
        if self.pipe is None:
            return
        self.pipe.unfuse_lora()
        self.pipe.unload_lora_weights()
        print("[ArtGenerator] LoRA 已卸载")

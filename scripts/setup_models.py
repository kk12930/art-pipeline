#!/usr/bin/env python3
# scripts/setup_models.py
# 模型检查与下载指引脚本
# 检查所需模型是否已下载，并提供下载说明

import sys
import os
from pathlib import Path

# 确保项目根目录在 Python 路径中
sys.path.insert(0, str(Path(__file__).parent.parent))


# 所需模型列表
REQUIRED_MODELS = [
    {
        "name": "SDXL 基础模型",
        "description": "Stable Diffusion XL 基础模型（约 6.6 GB）",
        "type": "huggingface",
        "model_id": "stabilityai/stable-diffusion-xl-base-1.0",
        "local_check": None,  # diffusers 会自动缓存，无需手动检查
        "download_cmd": (
            "# 方法 1：通过 diffusers（首次运行 generate.py 时自动下载）\n"
            "# 方法 2：手动下载（推荐，速度更快）\n"
            "pip install huggingface_hub\n"
            "huggingface-cli download stabilityai/stable-diffusion-xl-base-1.0 "
            "--local-dir models/sdxl-base"
        ),
        "note": "首次运行 generate.py 时会自动下载（需要科学上网），也可提前手动下载",
    },
    {
        "name": "SDXL VAE（fp16）",
        "description": "SDXL 配套 VAE 模型，提升图片质量（约 320 MB）",
        "type": "huggingface",
        "model_id": "madebyollin/sdxl-vae-fp16-fix",
        "local_check": None,
        "download_cmd": (
            "huggingface-cli download madebyollin/sdxl-vae-fp16-fix "
            "--local-dir models/sdxl-vae"
        ),
        "note": "可选，但强烈推荐，能显著减少图片噪点",
    },
    {
        "name": "SAM ViT-H（用于 UI 拆解）",
        "description": "Segment Anything Model 最高精度版本（约 2.4 GB）",
        "type": "direct",
        "model_id": "sam_vit_h_4b8939.pth",
        "local_check": "models/sam/sam_vit_h_4b8939.pth",
        "download_cmd": (
            "# 方法 1：使用 wget\n"
            "wget -P models/sam/ "
            "https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth\n\n"
            "# 方法 2：使用 curl\n"
            "mkdir -p models/sam && curl -L "
            "https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth "
            "-o models/sam/sam_vit_h_4b8939.pth"
        ),
        "note": "阶段三（UI 拆解）必需。如果只需要生成功能可以暂时跳过",
    },
    {
        "name": "Real-ESRGAN x4plus（超分辨率）",
        "description": "Real-ESRGAN 超分辨率模型（约 67 MB）",
        "type": "direct",
        "model_id": "RealESRGAN_x4plus.pth",
        "local_check": "models/esrgan/RealESRGAN_x4plus.pth",
        "download_cmd": (
            "mkdir -p models/esrgan\n"
            "wget -P models/esrgan/ "
            "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth"
        ),
        "note": "阶段四（后处理）必需。用于图片超分辨率放大",
    },
]


def check_model(model_info: dict) -> bool:
    """
    检查模型是否已下载。

    Args:
        model_info: 模型信息字典。

    Returns:
        True 表示已就绪，False 表示需要下载。
    """
    if model_info["local_check"] is None:
        # Hugging Face 模型无法简单检查，假设需要提示
        return False

    local_path = Path(model_info["local_check"])
    return local_path.exists()


def check_dependencies() -> dict:
    """
    检查所有 Python 依赖是否已安装。

    Returns:
        字典，键为包名，值为 (已安装, 版本) 元组。
    """
    packages = {
        "torch": "PyTorch（核心深度学习框架）",
        "diffusers": "Diffusers（SDXL 推理）",
        "transformers": "Transformers（模型加载）",
        "PIL": "Pillow（图片处理）",
        "yaml": "PyYAML（配置文件解析）",
        "tqdm": "tqdm（进度条）",
        "segment_anything": "Segment Anything（UI 拆解，阶段三）",
        "cv2": "OpenCV（图像处理，阶段三）",
        "realesrgan": "Real-ESRGAN（超分辨率，阶段四）",
    }

    results = {}
    for pkg_import, pkg_desc in packages.items():
        try:
            module = __import__(pkg_import)
            version = getattr(module, "__version__", "已安装")
            results[pkg_desc] = (True, version)
        except ImportError:
            results[pkg_desc] = (False, None)

    return results


def print_separator(char="-", width=60):
    print(char * width)


def main():
    print("=" * 60)
    print("🔧 美术工业管线 - 环境检查与模型下载指引")
    print("=" * 60)
    print()

    # 1. 检查 Python 依赖
    print("📦 Python 依赖检查")
    print_separator()
    dep_results = check_dependencies()
    all_core_installed = True
    for pkg_desc, (installed, version) in dep_results.items():
        status = f"✅ {version}" if installed else "❌ 未安装"
        print(f"  {'':2}{pkg_desc:<40} {status}")
        # 核心依赖：torch、diffusers、transformers、PIL、yaml
        is_core = any(
            kw in pkg_desc
            for kw in ["PyTorch", "Diffusers", "Transformers", "Pillow", "PyYAML"]
        )
        if is_core and not installed:
            all_core_installed = False
    print()

    if not all_core_installed:
        print("⚠️  请先安装核心依赖：")
        print("  pip install -r requirements.txt")
        print()

    # 2. 检查模型文件
    print("🤖 模型文件检查")
    print_separator()
    all_downloaded = True
    missing_models = []
    for model_info in REQUIRED_MODELS:
        is_ready = check_model(model_info)
        if model_info["local_check"] is None:
            status = "❓ 需确认（自动下载）"
        elif is_ready:
            status = "✅ 已下载"
        else:
            status = "❌ 未下载"
            all_downloaded = False
            missing_models.append(model_info)
        print(f"  {model_info['name']:<30} {status}")
        print(f"  {'':2}{model_info['description']}")
        if model_info.get("note"):
            print(f"  {'':2}💡 {model_info['note']}")
        print()

    # 3. 显示下载指引
    if missing_models:
        print("📥 下载指引")
        print_separator()
        for model_info in missing_models:
            print(f"\n【{model_info['name']}】")
            print(f"  {model_info['description']}")
            print("  下载命令：")
            for line in model_info["download_cmd"].split("\n"):
                print(f"    {line}")
        print()

    # 4. CUDA 环境检查
    print("🖥️  GPU 环境检查")
    print_separator()
    try:
        import torch
        print(f"  PyTorch 版本: {torch.__version__}")
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            print(f"  GPU: {gpu_name}")
            print(f"  显存: {gpu_memory:.1f} GB")
            print(f"  CUDA 版本: {torch.version.cuda}")
            if gpu_memory < 12:
                print("  ⚠️  显存低于 12GB，可能无法运行 SDXL，建议减小生成分辨率")
            elif gpu_memory < 16:
                print("  ℹ️  12~16GB 显存，建议开启所有显存优化（已默认开启）")
            else:
                print("  ✅ 显存充足")
        else:
            print("  ⚠️  未检测到 CUDA GPU，将使用 CPU 运行（速度非常慢）")
    except ImportError:
        print("  ❌ PyTorch 未安装")
    print()

    # 5. 快速开始
    print("🚀 快速开始")
    print_separator()
    print("  # 1. 安装依赖")
    print("  conda create -n art-pipeline python=3.10")
    print("  conda activate art-pipeline")
    print("  pip install torch==2.2.2+cu121 torchvision --index-url https://download.pytorch.org/whl/cu121")
    print("  pip install -r requirements.txt")
    print()
    print("  # 2. 生成图标")
    print("  python scripts/generate.py '金色宝剑' --type icon --size medium")
    print()
    print("  # 3. 生成 UI 设计图")
    print("  python scripts/generate.py '奇幻风格主界面' --type ui_design --size mobile_portrait")
    print()
    print("  # 4. 拆解 UI 图片（需先下载 SAM 权重）")
    print("  python scripts/decompose.py outputs/ui_design_xxx.png")
    print()

    if all_downloaded and all_core_installed:
        print("✅ 环境就绪，可以开始使用！")
    else:
        print("⚠️  请按照上面的指引完成环境配置后再使用")


if __name__ == "__main__":
    main()

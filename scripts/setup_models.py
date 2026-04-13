"""
模型下载/检查脚本
检查各模型文件是否已存在，并打印下载指引
"""

import sys
from pathlib import Path

# 将项目根目录加入 sys.path
_PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))


# 需要检查的模型文件及下载信息
_MODELS = [
    {
        "name": "SDXL Base Model (via diffusers)",
        "type": "huggingface",
        "path": None,  # diffusers 自动缓存，无需手动下载
        "description": "Stable Diffusion XL 基础模型",
        "install": "自动通过 HuggingFace Hub 下载，首次运行 generate.py 时自动缓存",
        "model_id": "stabilityai/stable-diffusion-xl-base-1.0",
        "link": "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0",
    },
    {
        "name": "SAM (Segment Anything Model)",
        "type": "file",
        "path": "models/sam/sam_vit_h.pth",
        "description": "用于 UI 拆解的图像分割模型",
        "install": "手动下载后放入 models/sam/ 目录",
        "link": "https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth",
        "size": "~2.4 GB",
    },
    {
        "name": "Real-ESRGAN x4plus",
        "type": "file",
        "path": "models/realesrgan/RealESRGAN_x4plus.pth",
        "description": "用于图片超分辨率放大的模型",
        "install": "手动下载后放入 models/realesrgan/ 目录",
        "link": "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth",
        "size": "~67 MB",
    },
]


def check_file(path: str) -> bool:
    """检查文件是否存在"""
    return Path(path).exists()


def print_separator(char: str = "-", width: int = 60) -> None:
    """打印分隔线"""
    print(char * width)


def main() -> None:
    """检查所有模型文件，打印状态和下载指引"""
    print("=" * 60)
    print("  Art-Pipeline 模型检查工具")
    print("=" * 60)
    print()

    all_ok = True

    for model in _MODELS:
        print_separator()
        print(f"📦 {model['name']}")
        print(f"   描述: {model['description']}")

        if model["type"] == "huggingface":
            # HuggingFace 模型通过 diffusers 自动缓存，检查 HF_HOME
            hf_home = Path.home() / ".cache" / "huggingface" / "hub"
            # 简单检查缓存目录是否有相关内容
            model_slug = model["model_id"].replace("/", "--")
            cached_dir = hf_home / f"models--{model_slug}"
            if cached_dir.exists():
                print(f"   状态: ✅ 已缓存（{cached_dir}）")
            else:
                all_ok = False
                print(f"   状态: ⚠️  尚未缓存（首次运行时自动下载）")
            print(f"   模型 ID: {model['model_id']}")
            print(f"   链接: {model['link']}")

        else:
            # 本地文件模型
            file_path = _PROJECT_ROOT / model["path"]
            exists = check_file(file_path)

            if exists:
                size_mb = file_path.stat().st_size / 1024 / 1024
                print(f"   状态: ✅ 已存在（{size_mb:.1f} MB）")
            else:
                all_ok = False
                print(f"   状态: ❌ 文件不存在")
                print(f"   路径: {file_path}")
                print(f"   大小: {model.get('size', '未知')}")
                print(f"\n   📥 下载方式：{model['install']}")
                print(f"   🔗 下载链接: {model['link']}")
                print(f"\n   命令示例：")
                print(f"     mkdir -p {file_path.parent}")
                print(f"     wget -O {file_path} '{model['link']}'")

        print()

    print_separator("=")
    if all_ok:
        print("✅ 所有模型已就绪，可以开始使用！")
    else:
        print("⚠️  部分模型尚未下载，请按照上方指引进行下载。")
        print()
        print("💡 快速下载命令（SAM 模型）：")
        print("   mkdir -p models/sam")
        print(
            "   wget -O models/sam/sam_vit_h.pth "
            "https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth"
        )
        print()
        print("💡 快速下载命令（Real-ESRGAN 模型）：")
        print("   mkdir -p models/realesrgan")
        print(
            "   wget -O models/realesrgan/RealESRGAN_x4plus.pth "
            "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth"
        )
    print("=" * 60)


if __name__ == "__main__":
    main()

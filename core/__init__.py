# core/__init__.py
# 美术工业管线核心模块包
# 使用懒导入避免在缺少可选依赖（如 torch）时导入报错

from core.presets import PresetManager
from core.prompt_builder import PromptBuilder

# ArtGenerator 依赖 torch/diffusers，懒导入以避免未安装时崩溃。
# 请在使用前检查 torch 和 diffusers 已安装，
# 或捕获 ImportError：from core.generator import ArtGenerator
try:
    from core.generator import ArtGenerator
    _ARTGENERATOR_AVAILABLE = True
except ImportError as _artgen_err:
    _artgen_err_msg = str(_artgen_err)
    _ARTGENERATOR_AVAILABLE = False

    class ArtGenerator:  # type: ignore[no-redef]
        """占位类：torch/diffusers 未安装时提供友好的错误提示。"""
        def __init__(self, *args, **kwargs):
            raise ImportError(
                f"ArtGenerator 需要安装 torch 和 diffusers：\n"
                f"  pip install torch diffusers>=0.27.0 transformers>=4.38.0\n"
                f"原始错误: {_artgen_err_msg}"
            )


__all__ = ["ArtGenerator", "PresetManager", "PromptBuilder"]

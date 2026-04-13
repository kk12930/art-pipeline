"""
art-pipeline 核心模块包
导出主要类供外部使用

注意：ArtGenerator 和 PostProcessor 依赖 torch/diffusers/realesrgan 等重型库，
仅在对应库已安装时才能正常导入。PresetManager 和 PromptBuilder 无重型依赖，随时可用。
"""

from .presets import PresetManager
from .prompt_builder import PromptBuilder

# 有重型依赖的模块做延迟导入，缺少依赖时不影响其他功能
try:
    from .generator import ArtGenerator
except ImportError:
    pass  # torch / diffusers 未安装时跳过

try:
    from .post_processor import PostProcessor
except ImportError:
    pass  # realesrgan / basicsr 未安装时跳过

__all__ = [
    "ArtGenerator",
    "PresetManager",
    "PromptBuilder",
    "PostProcessor",
]

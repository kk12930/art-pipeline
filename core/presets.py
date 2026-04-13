# core/presets.py
# 预设管理器
# 负责从 configs/ 目录加载 YAML 预设文件，并提供尺寸查询和提示词构建功能

import os
from pathlib import Path
import yaml


# 项目根目录（configs/ 目录的父目录）
_PROJECT_ROOT = Path(__file__).parent.parent


class PresetManager:
    """
    预设管理器，负责加载和解析 YAML 预设配置文件。

    支持的预设类型：
    - "icon"       → configs/icon_preset.yaml
    - "ui_design"  → configs/ui_design_preset.yaml
    """

    # 预设类型到配置文件的映射
    PRESET_FILES = {
        "icon": "icon_preset.yaml",
        "ui_design": "ui_design_preset.yaml",
    }

    def __init__(self, configs_dir: str = None):
        """
        初始化预设管理器。

        Args:
            configs_dir: 配置文件目录路径。为 None 时自动使用项目根目录下的 configs/。
        """
        self.configs_dir = Path(configs_dir) if configs_dir else _PROJECT_ROOT / "configs"
        self._cache: dict = {}  # 已加载预设的缓存，避免重复读取文件

    def load(self, preset_type: str) -> dict:
        """
        加载指定类型的预设配置。

        Args:
            preset_type: 预设类型，支持 "icon" 或 "ui_design"。

        Returns:
            包含预设配置的字典。

        Raises:
            ValueError: 不支持的预设类型。
            FileNotFoundError: 配置文件不存在。
        """
        if preset_type in self._cache:
            return self._cache[preset_type]

        if preset_type not in self.PRESET_FILES:
            raise ValueError(
                f"不支持的预设类型: '{preset_type}'，"
                f"可用类型: {list(self.PRESET_FILES.keys())}"
            )

        config_path = self.configs_dir / self.PRESET_FILES[preset_type]
        if not config_path.exists():
            raise FileNotFoundError(f"预设配置文件不存在: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            preset = yaml.safe_load(f)

        self._cache[preset_type] = preset
        return preset

    def get_size(self, preset_type: str, size_name: str) -> tuple[int, int]:
        """
        获取指定预设中某个尺寸名称对应的宽高。

        Args:
            preset_type: 预设类型，如 "icon" 或 "ui_design"。
            size_name: 尺寸名称，如 "medium"（icon）或 "mobile_portrait"（ui_design）。

        Returns:
            (width, height) 元组，单位为像素。

        Raises:
            KeyError: 指定的尺寸名称不存在于预设中。
        """
        preset = self.load(preset_type)
        sizes = preset.get("sizes", {})

        if size_name not in sizes:
            available = list(sizes.keys())
            raise KeyError(
                f"尺寸 '{size_name}' 不存在于预设 '{preset_type}' 中，"
                f"可用尺寸: {available}"
            )

        size_config = sizes[size_name]
        return size_config["width"], size_config["height"]

    def get_internal_size(self, preset_type: str) -> tuple[int, int]:
        """
        获取指定预设的内部生成分辨率（SDXL 实际生成时使用的尺寸）。

        Args:
            preset_type: 预设类型。

        Returns:
            (internal_width, internal_height) 元组。
        """
        preset = self.load(preset_type)
        return preset.get("internal_width", 1024), preset.get("internal_height", 1024)

    def build_prompt(self, preset_type: str, user_prompt: str) -> str:
        """
        使用预设中的提示词模板，将用户输入填入模板生成完整提示词。

        Args:
            preset_type: 预设类型。
            user_prompt: 用户输入的提示词描述（如 "金色宝剑"、"蓝色魔法按钮"）。

        Returns:
            填充完成的完整提示词字符串。
        """
        preset = self.load(preset_type)
        template = preset.get("prompt_template", "{user_prompt}")
        # 替换模板中的占位符
        return template.replace("{user_prompt}", user_prompt).strip()

    def get_negative_prompt(self, preset_type: str) -> str:
        """
        获取预设中的负面提示词。

        Args:
            preset_type: 预设类型。

        Returns:
            负面提示词字符串。
        """
        preset = self.load(preset_type)
        return preset.get("negative_prompt", "").strip()

    def get_defaults(self, preset_type: str) -> dict:
        """
        获取预设中的默认生成参数（steps、guidance_scale 等）。

        Args:
            preset_type: 预设类型。

        Returns:
            包含默认参数的字典。
        """
        preset = self.load(preset_type)
        return preset.get("defaults", {})

    def list_sizes(self, preset_type: str) -> list[str]:
        """
        列出指定预设中所有可用的尺寸名称。

        Args:
            preset_type: 预设类型。

        Returns:
            尺寸名称列表。
        """
        preset = self.load(preset_type)
        return list(preset.get("sizes", {}).keys())

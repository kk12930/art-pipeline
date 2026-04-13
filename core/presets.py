"""
预设管理器
负责加载和解析 YAML 预设配置文件，提供尺寸查询和提示词构建功能
"""

import os
from pathlib import Path
from typing import Optional, Tuple

import yaml


# configs 目录相对于本文件的路径
_CONFIGS_DIR = Path(__file__).parent.parent / "configs"

# 预设类型到文件名的映射
_PRESET_FILES = {
    "icon": "icon_preset.yaml",
    "ui_design": "ui_design_preset.yaml",
}


class PresetManager:
    """
    预设管理器
    负责加载 YAML 预设文件，提供尺寸信息和提示词模板
    """

    def __init__(self, configs_dir: Optional[str] = None):
        """
        初始化预设管理器

        Args:
            configs_dir: 配置文件目录路径，默认使用项目内的 configs/ 目录
        """
        self.configs_dir = Path(configs_dir) if configs_dir else _CONFIGS_DIR
        self._data: dict = {}

    def load(self, preset_type: str) -> "PresetManager":
        """
        从 configs/ 目录加载对应的 YAML 预设

        Args:
            preset_type: 预设类型，支持 "icon" 或 "ui_design"

        Returns:
            self，支持链式调用

        Raises:
            ValueError: 不支持的预设类型
            FileNotFoundError: 配置文件不存在
        """
        if preset_type not in _PRESET_FILES:
            raise ValueError(
                f"不支持的预设类型: '{preset_type}'，可选: {list(_PRESET_FILES.keys())}"
            )

        config_path = self.configs_dir / _PRESET_FILES[preset_type]
        if not config_path.exists():
            raise FileNotFoundError(f"预设文件不存在: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            self._data = yaml.safe_load(f)

        print(f"[信息] 已加载预设: {preset_type} ({config_path.name})")
        return self

    def get_size(self, size_name: str) -> Tuple[int, int]:
        """
        获取指定尺寸预设的宽高

        Args:
            size_name: 尺寸名称，如 "small"、"medium"、"mobile_portrait" 等

        Returns:
            (width, height) 元组

        Raises:
            KeyError: 找不到指定的尺寸名称
        """
        sizes = self._data.get("sizes", [])
        for size in sizes:
            if size["name"] == size_name:
                return size["width"], size["height"]
        available = [s["name"] for s in sizes]
        raise KeyError(f"找不到尺寸 '{size_name}'，可选: {available}")

    def get_internal_resolution(self) -> Tuple[int, int]:
        """
        获取内部生成分辨率（SDXL 推理时使用，之后再缩放到目标尺寸）

        Returns:
            (width, height) 元组
        """
        res = self._data.get("internal_resolution", {"width": 1024, "height": 1024})
        return res["width"], res["height"]

    def build_prompt(self, user_prompt: str) -> str:
        """
        用预设模板填充用户提示词

        Args:
            user_prompt: 用户输入的核心描述

        Returns:
            填充模板后的完整提示词
        """
        template = self._data.get("prompt_template", "{prompt}")
        # YAML 多行字符串可能带换行，先去掉多余空白
        template = " ".join(template.split())
        return template.format(prompt=user_prompt)

    @property
    def negative_prompt(self) -> str:
        """
        获取预设的负面提示词

        Returns:
            负面提示词字符串
        """
        neg = self._data.get("default_negative_prompt", "")
        # 去掉多余的换行和空白
        return " ".join(neg.split())

    @property
    def name(self) -> str:
        """预设名称"""
        return self._data.get("name", "")

    @property
    def description(self) -> str:
        """预设描述"""
        return self._data.get("description", "")

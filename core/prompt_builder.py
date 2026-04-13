"""
提示词构建器
负责将用户输入填入模板，以及合并多个负面提示词
"""

from typing import Optional


class PromptBuilder:
    """
    提示词构建器
    提供模板填充和负面提示词合并功能
    """

    def build(self, template: str, user_input: str) -> str:
        """
        将用户输入填入模板

        Args:
            template:   包含 {prompt} 占位符的模板字符串
            user_input: 用户输入的核心描述

        Returns:
            填充后的完整提示词字符串
        """
        # 先将模板中多余的空白（换行等）规范化
        template = " ".join(template.split())
        return template.format(prompt=user_input)

    def merge_negative(
        self,
        preset_negative: str,
        user_negative: Optional[str] = None,
    ) -> str:
        """
        合并预设负面提示词与用户自定义负面提示词

        Args:
            preset_negative: 预设中的负面提示词
            user_negative:   用户额外指定的负面提示词，可为 None 或空字符串

        Returns:
            合并后的负面提示词字符串（去重、去空、逗号分隔）
        """
        # 拆分各自的词条，去除空白和重复项
        preset_parts = [p.strip() for p in preset_negative.split(",") if p.strip()]
        user_parts: list[str] = []
        if user_negative:
            user_parts = [p.strip() for p in user_negative.split(",") if p.strip()]

        # 保留顺序去重：预设词条在前，用户词条中不重复的追加到后面
        seen: set[str] = set()
        merged: list[str] = []
        for part in preset_parts + user_parts:
            lower = part.lower()
            if lower not in seen:
                seen.add(lower)
                merged.append(part)

        return ", ".join(merged)

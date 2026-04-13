# core/prompt_builder.py
# 提示词构建器
# 负责模板填充、正面/负面提示词的合并与处理

class PromptBuilder:
    """
    提示词构建器，负责将用户输入填入模板，并合并负面提示词。

    典型用法：
        builder = PromptBuilder()
        prompt = builder.build("game UI icon, {user_input}, vibrant colors", "金色宝剑")
        neg = builder.merge_negative("blurry, low quality", "text, watermark")
    """

    def build(self, template: str, user_input: str) -> str:
        """
        将用户输入填入提示词模板中。

        模板中使用 {user_input} 作为占位符，会被替换为用户提供的描述。
        如果模板中不包含 {user_input}，则将用户输入追加到模板末尾。

        Args:
            template: 提示词模板字符串，包含 {user_input} 占位符。
            user_input: 用户输入的描述文字（如 "金色宝剑"、"蓝色魔法按钮"）。

        Returns:
            填充完成的完整提示词字符串。

        Examples:
            >>> builder = PromptBuilder()
            >>> builder.build("game icon, {user_input}, vibrant", "gold sword")
            'game icon, gold sword, vibrant'
        """
        user_input = user_input.strip()
        if "{user_input}" in template:
            return template.replace("{user_input}", user_input).strip()
        # 模板不含占位符时，将用户输入追加到末尾
        return f"{template.strip()}, {user_input}"

    def merge_negative(self, preset_negative: str, user_negative: str = "") -> str:
        """
        合并预设负面提示词和用户自定义负面提示词。

        去重后以逗号分隔合并，避免重复项占用 token。

        Args:
            preset_negative: 预设配置中的负面提示词（通常来自 YAML 配置）。
            user_negative: 用户额外指定的负面提示词。为空时仅返回预设负面提示词。

        Returns:
            合并后的负面提示词字符串。

        Examples:
            >>> builder = PromptBuilder()
            >>> builder.merge_negative("blurry, low quality", "text, blurry")
            'blurry, low quality, text'
        """
        # 拆分为单独的词条并去除首尾空格
        preset_items = [item.strip() for item in preset_negative.split(",") if item.strip()]
        user_items = [item.strip() for item in user_negative.split(",") if item.strip()]

        # 合并并去重（保持原有顺序，用 set 过滤重复项）
        seen = set()
        merged = []
        for item in preset_items + user_items:
            item_lower = item.lower()
            if item_lower not in seen:
                seen.add(item_lower)
                merged.append(item)

        return ", ".join(merged)

    def sanitize(self, prompt: str) -> str:
        """
        清理提示词：去除多余空格、换行符，规范化标点符号。

        Args:
            prompt: 原始提示词字符串。

        Returns:
            清理后的提示词字符串。
        """
        # 将换行替换为逗号，压缩多余空白
        prompt = prompt.replace("\n", ", ").replace("  ", " ")
        # 清理多余的逗号
        parts = [p.strip() for p in prompt.split(",") if p.strip()]
        return ", ".join(parts)

    def add_quality_tags(self, prompt: str, quality: str = "high") -> str:
        """
        在提示词末尾追加质量标签，提升生成图片质量。

        Args:
            prompt: 原始提示词。
            quality: 质量级别，支持 "high"（高质量）或 "ultra"（超高质量）。

        Returns:
            追加质量标签后的提示词。
        """
        quality_tags = {
            "high": "high quality, detailed, masterpiece",
            "ultra": "ultra high quality, extremely detailed, masterpiece, best quality, 8k",
        }
        tags = quality_tags.get(quality, quality_tags["high"])
        return f"{prompt.rstrip(', ')}, {tags}"

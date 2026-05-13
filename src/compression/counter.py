"""Token 计数工具"""

from typing import List, Optional

import tiktoken
from langchain_core.messages import BaseMessage
from loguru import logger


class TokenCounter:
    """精确 token 计数（使用 tiktoken）"""

    def __init__(self, encoding_name: str = "cl100k_base") -> None:
        try:
            self._encoding = tiktoken.get_encoding(encoding_name)
        except Exception:
            self._encoding = tiktoken.get_encoding("cl100k_base")
        self._model = encoding_name

    def count_text(self, text: str) -> int:
        """计算文本 token 数"""
        return len(self._encoding.encode(text))

    def count_messages(self, messages: List[BaseMessage]) -> int:
        """计算消息列表总 token 数"""
        total = 0
        for msg in messages:
            content = str(msg.content) if hasattr(msg, "content") else str(msg)
            total += self.count_text(content)
        return total

    def estimate(self, text: str) -> int:
        """快速估算（中文按字，英文按空格）"""
        if not text:
            return 0
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        words = len(text.split())
        return chinese_chars + words

    def would_exceed(self, text: str, current_tokens: int, limit: int) -> bool:
        """判断添加文本后是否会超限"""
        return current_tokens + self.count_text(text) > limit

"""L0 — 滑动窗口缓冲记忆"""

from typing import List, Optional

import tiktoken
from langchain_core.messages import BaseMessage
from loguru import logger

from src.core.config import get_config


class BufferMemory:
    """L0 感知记忆 — 当前会话的滑动窗口"""

    def __init__(self, max_tokens: Optional[int] = None) -> None:
        config = get_config()
        self._max_tokens = max_tokens or config.memory.buffer_max_tokens
        self._messages: List[BaseMessage] = []
        self._encoding = tiktoken.get_encoding("cl100k_base")

    @property
    def messages(self) -> List[BaseMessage]:
        return list(self._messages)

    def add(self, message: BaseMessage) -> None:
        self._messages.append(message)
        self._trim()

    def get_recent(self, n: Optional[int] = None) -> List[BaseMessage]:
        if n is None:
            return list(self._messages)
        return self._messages[-n:]

    def token_count(self) -> int:
        total = 0
        for msg in self._messages:
            text = str(msg.content) if hasattr(msg, "content") else str(msg)
            total += len(self._encoding.encode(text))
        return total

    def _trim(self) -> None:
        while self.token_count() > self._max_tokens and len(self._messages) > 2:
            removed = self._messages.pop(0)
            logger.debug(f"L0 buffer 淘汰旧消息: {str(removed)[:50]}...")

    def clear(self) -> None:
        self._messages.clear()

    def to_string(self, max_messages: Optional[int] = None) -> str:
        msgs = self._messages[-max_messages:] if max_messages else self._messages
        lines = []
        for msg in msgs:
            role = getattr(msg, "type", "unknown")
            content = str(msg.content) if hasattr(msg, "content") else str(msg)
            lines.append(f"[{role}]: {content}")
        return "\n".join(lines)

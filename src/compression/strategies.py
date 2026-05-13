"""上下文压缩策略"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from langchain_core.language_models import BaseChatModel
from loguru import logger

from src.compression.counter import TokenCounter
from src.core.config import get_config


class CompressionStrategy(ABC):
    """压缩策略基类"""

    @abstractmethod
    def compress(self, context: str, token_limit: int, **kwargs) -> str:
        ...

    @abstractmethod
    def should_apply(self, current_tokens: int, token_limit: int) -> bool:
        ...


class WindowStrategy(CompressionStrategy):
    """窗口截断 — 保留最近的内容"""

    def __init__(self, counter: Optional[TokenCounter] = None) -> None:
        self._counter = counter or TokenCounter()

    def should_apply(self, current_tokens: int, token_limit: int) -> bool:
        return current_tokens > token_limit * 0.8

    def compress(self, context: str, token_limit: int, **kwargs) -> str:
        """从后往前截取，保留最近的消息"""
        lines = context.split("\n")
        result = ""
        for line in reversed(lines):
            candidate = line + "\n" + result if result else line
            if self._counter.count_text(candidate) > token_limit:
                break
            result = candidate
        return result.strip() or context[-int(token_limit * 4):]


class SummarizeStrategy(CompressionStrategy):
    """摘要压缩 — 用 LLM 生成摘要"""

    def __init__(self, summarizer: Optional[Any] = None) -> None:
        from src.compression.summarizer import Summarizer

        self._summarizer = summarizer

    def set_llm(self, llm: BaseChatModel) -> None:
        from src.compression.summarizer import Summarizer

        self._summarizer = Summarizer(llm)

    def should_apply(self, current_tokens: int, token_limit: int) -> bool:
        return current_tokens > token_limit

    def compress(self, context: str, token_limit: int, **kwargs) -> str:
        if self._summarizer is None:
            logger.warning("SummarizeStrategy 缺少 LLM，降级为窗口截断")
            return WindowStrategy().compress(context, token_limit)

        config = get_config()
        max_tokens = config.compression.summary_max_tokens
        return self._summarizer.summarize_text(context, max_tokens=max_tokens)


class RetrieveStrategy(CompressionStrategy):
    """检索压缩 — 仅保留与当前问题最相关的片段"""

    def __init__(self, vector_store=None) -> None:
        self._vector_store = vector_store
        self._counter = TokenCounter()

    def should_apply(self, current_tokens: int, token_limit: int) -> bool:
        return current_tokens > token_limit

    def compress(self, context: str, token_limit: int, **kwargs) -> str:
        query = kwargs.get("query", "")
        if not self._vector_store or not query:
            return WindowStrategy(self._counter).compress(context, token_limit)

        results = self._vector_store.search(query, top_k=5)
        compressed = "\n".join(
            r.get("content", "")[:500] for r in results
        )

        if self._counter.count_text(compressed) > token_limit:
            compressed = compressed[:token_limit * 4]

        return compressed

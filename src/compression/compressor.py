"""上下文压缩管线 — 编排多种压缩策略"""

from typing import Optional

from langchain_core.language_models import BaseChatModel
from loguru import logger

from src.compression.counter import TokenCounter
from src.compression.strategies import (
    RetrieveStrategy,
    SummarizeStrategy,
    WindowStrategy,
)
from src.core.config import get_config


class ContextCompressor:
    """上下文压缩器 — 按策略优先级压缩上下文"""

    def __init__(self, llm: BaseChatModel) -> None:
        self._config = get_config()
        self._counter = TokenCounter()
        self._strategies = {
            "window": WindowStrategy(self._counter),
            "summarize": SummarizeStrategy(),
            "retrieve": RetrieveStrategy(),
        }
        self._strategies["summarize"].set_llm(llm)

    def compress(self, context: str, query: str = "") -> str:
        """执行压缩管线"""
        current_tokens = self._counter.count_text(context)
        limit = self._config.compression.max_context_tokens

        if current_tokens <= limit:
            return context

        logger.info(f"触发压缩: {current_tokens} tokens → 目标 ≤ {limit} tokens")

        result = context
        for strategy_name in self._config.compression.strategy_sequence:
            strategy = self._strategies.get(strategy_name)
            if strategy is None:
                continue

            current = self._counter.count_text(result)
            if not strategy.should_apply(current, limit):
                continue

            logger.debug(f"应用策略: {strategy_name}")
            result = strategy.compress(result, limit, query=query)

            if self._counter.count_text(result) <= limit:
                break

        final_tokens = self._counter.count_text(result)
        logger.info(f"压缩完成: {current_tokens} → {final_tokens} tokens")

        return result

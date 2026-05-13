"""L1 — 对话摘要记忆（跨会话持久化）"""

from datetime import datetime
from typing import List, Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from loguru import logger


class SummaryMemory:
    """L1 摘要记忆 — 压缩历史对话为摘要"""

    def __init__(self, llm: BaseChatModel, max_summaries: int = 50) -> None:
        self._llm = llm
        self._max_summaries = max_summaries
        self._summaries: List[dict] = []

    @property
    def summaries(self) -> List[dict]:
        return self._summaries

    def summarize_messages(self, messages: List[BaseMessage]) -> str:
        """将一组消息压缩为摘要"""
        if not messages:
            return ""

        conversation = "\n".join(
            f"{getattr(m, 'type', 'unknown')}: {m.content}" for m in messages
        )

        prompt = f"""请将以下对话浓缩为一段简洁的摘要，保留关键信息和决策：

对话内容：
{conversation}

摘要："""

        try:
            response = self._llm.invoke([HumanMessage(content=prompt)])
            summary = str(response.content)
            logger.debug(f"生成摘要: {summary[:100]}...")
        except Exception as e:
            logger.warning(f"摘要生成失败，使用原始截断: {e}")
            summary = conversation[:500] + "..."

        self._summaries.append({
            "content": summary,
            "timestamp": datetime.now().isoformat(),
            "message_count": len(messages),
        })

        if len(self._summaries) > self._max_summaries:
            self._summaries.pop(0)

        return summary

    def compress_summaries(self) -> str:
        """对所有摘要进行二次压缩"""
        if not self._summaries:
            return ""

        if len(self._summaries) == 1:
            return self._summaries[0]["content"]

        all_summaries = "\n".join(
            f"[{s['timestamp']}] {s['content']}" for s in self._summaries
        )

        prompt = f"""以下是一系列对话摘要的历史记录，请合并为一段连贯的总体摘要：

{all_summaries}

总体摘要："""

        try:
            response = self._llm.invoke([HumanMessage(content=prompt)])
            return str(response.content)
        except Exception as e:
            logger.warning(f"摘要压缩失败: {e}")
            return all_summaries[:1000]

    def to_string(self) -> str:
        return "\n---\n".join(
            f"[{s['timestamp']}] {s['content']}" for s in self._summaries[-5:]
        )

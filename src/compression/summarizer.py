"""LLM 摘要生成器"""

from typing import List, Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger


class Summarizer:
    """使用 LLM 生成文本摘要"""

    def __init__(self, llm: BaseChatModel) -> None:
        self._llm = llm

    def summarize_text(self, text: str, max_tokens: int = 500) -> str:
        """将长文本压缩为摘要"""
        if not text:
            return ""

        prompt = f"""请将以下内容压缩为简洁的摘要（保留关键信息、数字、决策）：

内容：
{text}

摘要（不超过 {max_tokens} tokens）："""

        try:
            response = self._llm.invoke([HumanMessage(content=prompt)])
            return str(response.content)[:max_tokens * 2]
        except Exception as e:
            logger.warning(f"摘要生成失败: {e}")
            return text[:max_tokens * 2]

    def summarize_messages(self, messages: List[str], max_tokens: int = 500) -> str:
        """压缩一组消息"""
        text = "\n".join(messages)
        return self.summarize_text(text, max_tokens)

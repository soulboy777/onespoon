"""记忆编排器 — 整合 L0/L1/L2/L3，提供统一接口"""

from typing import List, Optional, Tuple

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage

from src.core.config import get_config
from src.memory.base import EpisodeFragment, MemoryFragment
from src.memory.buffer import BufferMemory
from src.memory.episodic import EpisodicMemory
from src.memory.semantic import SemanticMemory
from src.memory.summary import SummaryMemory


class MemoryManager:
    """
    记忆编排器 — 统一管理四层记忆

    L0 — BufferMemory: 当前会话滑动窗口
    L1 — SummaryMemory: 对话摘要
    L2 — SemanticMemory: 语义向量记忆
    L3 — EpisodicMemory: 情景/任务记忆
    """

    def __init__(self, llm: Optional[BaseChatModel] = None) -> None:
        self._config = get_config()
        self._llm = llm
        self._buffer = BufferMemory()
        self._summary: Optional[SummaryMemory] = None
        if llm:
            self._summary = SummaryMemory(llm)
        self._semantic = SemanticMemory()
        self._episodic = EpisodicMemory()

    @property
    def buffer(self) -> BufferMemory:
        return self._buffer

    @property
    def semantic(self) -> SemanticMemory:
        return self._semantic

    @property
    def episodic(self) -> EpisodicMemory:
        return self._episodic

    # ---- L0 Buffer ----

    def add_to_buffer(self, message: BaseMessage) -> None:
        self._buffer.add(message)

    def get_recent_messages(self, n: int = 10) -> List[BaseMessage]:
        return self._buffer.get_recent(n)

    # ---- L2 Semantic ----

    def add_semantic(self, content: str, importance: float = 0.5, metadata: Optional[dict] = None) -> str:
        fragment = MemoryFragment(content=content, importance=importance, metadata=metadata)
        return self._semantic.add(fragment)

    def retrieve_semantic(self, query: str, top_k: Optional[int] = None) -> List[MemoryFragment]:
        k = top_k or self._config.memory.semantic_top_k
        return self._semantic.search(query, top_k=k)

    # ---- L3 Episodic ----

    def add_episode(self, task: str, result: str, steps: List[str], success: bool, lessons: str = "") -> str:
        episode = EpisodeFragment(task=task, result=result, steps=steps, success=success, lessons=lessons)
        return self._episodic.add(episode)

    def retrieve_episodic(self, query: str, top_k: Optional[int] = None) -> List[EpisodeFragment]:
        k = top_k or self._config.memory.episodic_top_k
        return self._episodic.search(query, top_k=k)

    # ---- Build Context ----

    def build_context_string(
        self,
        semantic_memories: List[MemoryFragment],
        episodic_memories: List[EpisodeFragment],
    ) -> str:
        """组装上下文字符串"""
        parts = []

        if semantic_memories:
            parts.append("## 相关记忆")
            for m in semantic_memories:
                parts.append(f"- {m.content[:200]}")

        if episodic_memories:
            parts.append("\n## 相关历史任务")
            for e in episodic_memories:
                status_icon = "✓" if e.success else "✗"
                parts.append(f"- [{status_icon}] {e.task}: {e.lessons[:100]}")

        return "\n".join(parts)

    def evaluate_importance(self, user_input: str, assistant_output: str) -> float:
        """评估对话的重要性（0~1）"""
        combined = (user_input + " " + assistant_output).lower()

        high_keywords = ["记住", "重要", "偏好", "密码", "地址", "规则", "记录", "保存"]
        medium_keywords = ["任务", "完成", "失败", "错误", "创建", "修改"]

        score = 0.1

        for kw in high_keywords:
            if kw in combined:
                score += 0.2

        for kw in medium_keywords:
            if kw in combined:
                score += 0.1

        if len(combined) > 200:
            score += 0.1

        return min(score, 1.0)

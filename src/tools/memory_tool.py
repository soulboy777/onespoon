"""记忆查询工具 — 让 Agent 主动查询自身记忆"""

from typing import Optional

from pydantic import BaseModel, Field

from src.tools.base import BaseTool


class MemoryQueryInput(BaseModel):
    query: str = Field(description="检索关键词或问题")
    memory_type: str = Field(
        default="semantic",
        description="记忆类型: semantic (语义记忆), episodic (情景/任务记忆)"
    )
    top_k: int = Field(default=5, description="返回条数")


class MemoryQueryTool(BaseTool):
    name: str = "query_memory"
    description: str = (
        "查询自身记忆库。参数: query (检索内容), memory_type (semantic 或 episodic), top_k (返回数量)"
    )
    args_schema: type[BaseModel] = MemoryQueryInput
    category: str = "memory"

    _memory_manager: Optional[object] = None

    def set_memory_manager(self, manager) -> None:
        self._memory_manager = manager

    def _run(
        self,
        query: str,
        memory_type: str = "semantic",
        top_k: int = 5,
    ) -> str:
        if self._memory_manager is None:
            return "记忆系统未初始化"

        if memory_type == "semantic":
            fragments = self._memory_manager.retrieve_semantic(query, top_k=top_k)
            if not fragments:
                return "未找到相关语义记忆"
            lines = ["## 语义记忆检索结果"]
            for i, frag in enumerate(fragments, 1):
                lines.append(f"{i}. [{frag.importance:.0%}] {frag.content[:200]}")
            return "\n".join(lines)

        elif memory_type == "episodic":
            episodes = self._memory_manager.retrieve_episodic(query, top_k=top_k)
            if not episodes:
                return "未找到相关任务记忆"
            lines = ["## 情景记忆检索结果"]
            for i, ep in enumerate(episodes, 1):
                status = "✓" if ep.success else "✗"
                lines.append(f"{i}. [{status}] {ep.task}: {ep.lessons[:100]}")
            return "\n".join(lines)

        else:
            return f"未知记忆类型: {memory_type}，可选 semantic / episodic"

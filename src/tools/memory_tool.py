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

    def _execute(self, query: str, memory_type: str = "semantic", top_k: int = 5) -> dict:
        if self._memory_manager is None:
            return {"status": "error", "error": "记忆系统未初始化"}

        if memory_type == "semantic":
            fragments = self._memory_manager.retrieve_semantic(query, top_k=top_k)
            results = [{"content": f.content[:200], "importance": f.importance} for f in fragments]
            return {"data": results, "action": "query_memory", "type": "semantic", "count": len(results)}

        elif memory_type == "episodic":
            episodes = self._memory_manager.retrieve_episodic(query, top_k=top_k)
            results = [{"task": e.task, "success": e.success, "lessons": e.lessons[:200]} for e in episodes]
            return {"data": results, "action": "query_memory", "type": "episodic", "count": len(results)}

        else:
            return {"status": "error", "error": f"未知记忆类型: {memory_type}"}

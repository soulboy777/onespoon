"""RAG 检索工具 — 让 Agent 查询知识库"""

from typing import Optional

from pydantic import BaseModel, Field

from src.tools.base import BaseTool


class RAGSearchInput(BaseModel):
    query: str = Field(description="检索查询内容")
    kb_name: str = Field(default="", description="知识库名称，留空表示搜索所有知识库")
    top_k: int = Field(default=5, description="返回结果条数")


class RAGListKBInput(BaseModel):
    pass


class RAGSearchTool(BaseTool):
    name: str = "search_knowledge"
    description: str = (
        "搜索知识库获取文档内容。参数: query (搜索内容), kb_name (知识库名，可选), top_k (返回条数)"
    )
    args_schema: type[BaseModel] = RAGSearchInput
    category: str = "rag"

    _manager = None

    def set_manager(self, manager) -> None:
        self._manager = manager

    def _run(self, query: str, kb_name: str = "", top_k: int = 5) -> str:
        if self._manager is None:
            return "RAG 知识库未初始化"

        try:
            if kb_name:
                results = self._manager.search(kb_name, query, top_k=top_k)
            else:
                results = self._manager.search_all(query, top_k=top_k)
        except Exception as e:
            return f"搜索知识库失败: {e}"

        if not results:
            return f"未在知识库中找到与 '{query}' 相关的内容"

        lines = [f"## 知识库搜索结果 ({len(results)} 条)"]
        for i, r in enumerate(results, 1):
            meta = r.get("metadata", {})
            source = meta.get("doc_title", meta.get("source", ""))
            lines.append(f"\n### 结果 {i} [{r.get('source', '')}]")
            if source:
                lines.append(f"**来源**: {source}")
            lines.append(r.get("content", "")[:500])

        return "\n".join(lines)


class RAGListKBTool(BaseTool):
    name: str = "list_knowledge_bases"
    description: str = "列出所有可用的知识库"
    args_schema: type[BaseModel] = RAGListKBInput
    category: str = "rag"

    _manager = None

    def set_manager(self, manager) -> None:
        self._manager = manager

    def _run(self) -> str:
        if self._manager is None:
            return "RAG 知识库未初始化"

        try:
            kbs = self._manager.list_all()
        except Exception as e:
            return f"获取知识库列表失败: {e}"

        if not kbs:
            return "当前没有可用的知识库"

        lines = ["## 可用知识库"]
        for kb in kbs:
            lines.append(
                f"- **{kb.name}**: {kb.description or '无描述'} "
                f"({kb.document_count or 0} 文档, {kb.chunk_count or 0} 分块)"
            )

        return "\n".join(lines)

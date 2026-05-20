"""RAG 检索工具 — 让 Agent 查询知识库"""

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

    def _execute(self, query: str, kb_name: str = "", top_k: int = 5) -> dict:
        if self._manager is None:
            return {"status": "error", "error": "RAG 知识库未初始化"}

        if kb_name:
            results = self._manager.search(kb_name, query, top_k=top_k)
        else:
            results = self._manager.search_all(query, top_k=top_k)

        items = [
            {
                "content": r.get("content", "")[:300],
                "source": r.get("metadata", {}).get("doc_title", ""),
                "score": r.get("score", 0),
            }
            for r in results
        ]
        return {"data": items, "action": "rag_search", "query": query, "count": len(items)}


class RAGListKBTool(BaseTool):
    name: str = "list_knowledge_bases"
    description: str = "列出所有可用的知识库"
    args_schema: type[BaseModel] = RAGListKBInput
    category: str = "rag"

    _manager = None

    def set_manager(self, manager) -> None:
        self._manager = manager

    def _execute(self) -> dict:
        if self._manager is None:
            return {"status": "error", "error": "RAG 知识库未初始化"}

        kbs = self._manager.list_all()
        items = [
            {"name": kb.name, "description": kb.description or "", "doc_count": kb.document_count or 0}
            for kb in kbs
        ]
        return {"data": items, "action": "list_kb", "count": len(items)}

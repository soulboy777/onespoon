"""L2 — 向量语义记忆（用户偏好、知识片段、重要事实）"""

from typing import List, Optional

from loguru import logger

from src.memory.base import MemoryFragment
from src.storage.vector_store import VectorStore


class SemanticMemory:
    """L2 语义记忆 — 基于向量检索的长期记忆"""

    def __init__(self, vector_store: Optional[VectorStore] = None) -> None:
        self._store = vector_store or VectorStore()
        self._collection_name = "semantic_memory"

    def add(self, fragment: MemoryFragment) -> str:
        """添加语义记忆片段"""
        metadata = fragment.metadata or {}
        metadata["importance"] = fragment.importance

        doc_id = self._store.add(
            content=fragment.content,
            metadata=metadata,
            collection=self._collection_name,
        )
        logger.debug(f"语义记忆已写入: {fragment.content[:50]}...")
        return doc_id

    def search(self, query: str, top_k: int = 5) -> List[MemoryFragment]:
        """向量检索相关记忆"""
        results = self._store.search(
            query=query,
            top_k=top_k,
            collection=self._collection_name,
        )

        fragments = []
        for doc in results:
            fragments.append(MemoryFragment(
                content=doc["content"],
                importance=doc.get("metadata", {}).get("importance", 0.5),
                metadata=doc.get("metadata", {}),
            ))

        return fragments

    def delete(self, doc_id: str) -> None:
        self._store.delete(doc_id, collection=self._collection_name)

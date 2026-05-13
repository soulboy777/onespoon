"""向量存储 — ChromaDB 封装"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings
from loguru import logger


class VectorStore:
    """ChromaDB 向量存储封装"""

    def __init__(self, persist_dir: Optional[str] = None) -> None:
        if persist_dir is None:
            from src.core.config import get_config

            config = get_config()
            persist_dir = config.storage.chroma_persist_dir

        if not os.path.isabs(persist_dir):
            project_root = Path(__file__).resolve().parent.parent.parent
            persist_dir = str(project_root / persist_dir)

        os.makedirs(persist_dir, exist_ok=True)

        self._client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False),
        )
        logger.info(f"ChromaDB 已连接: {persist_dir}")

    def get_or_create_collection(self, name: str):
        """获取或创建集合"""
        return self._client.get_or_create_collection(name=name)

    def add(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        doc_id: Optional[str] = None,
        collection: str = "default",
    ) -> str:
        """添加文档到向量库"""
        import uuid

        coll = self.get_or_create_collection(collection)
        doc_id = doc_id or str(uuid.uuid4())

        coll.add(
            documents=[content],
            metadatas=[metadata or {}],
            ids=[doc_id],
        )
        return doc_id

    def search(
        self,
        query: str,
        top_k: int = 5,
        collection: str = "default",
    ) -> List[Dict[str, Any]]:
        """向量检索"""
        coll = self.get_or_create_collection(collection)

        try:
            results = coll.query(
                query_texts=[query],
                n_results=top_k,
            )
        except Exception:
            logger.warning("ChromaDB 查询失败，返回空结果")
            return []

        docs = []
        if results.get("documents") and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                item = {"content": doc, "id": results["ids"][0][i]}
                if results.get("metadatas") and results["metadatas"][0]:
                    item["metadata"] = results["metadatas"][0][i] or {}
                docs.append(item)

        return docs

    def delete(self, doc_id: str, collection: str = "default") -> None:
        """删除文档"""
        coll = self.get_or_create_collection(collection)
        coll.delete(ids=[doc_id])

    def count(self, collection: str = "default") -> int:
        """集合中的文档数量"""
        coll = self.get_or_create_collection(collection)
        return coll.count()

    def clear(self, collection: str = "default") -> None:
        """清空集合"""
        self._client.delete_collection(name=collection)
        self.get_or_create_collection(collection)

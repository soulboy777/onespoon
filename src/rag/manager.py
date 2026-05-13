"""知识库管理器 — 增删改查知识库、文档"""

import json
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy.orm import joinedload

from src.core.config import get_config
from src.rag.database import get_session, init_rag_db
from src.rag.embedder import Embedder
from src.rag.ingestion import IngestionPipeline
from src.rag.models import Chunk, Document, KnowledgeBase
from src.rag.retriever import HybridRetriever
from src.storage.vector_store import VectorStore


class KnowledgeBaseManager:
    """知识库管理器"""

    def __init__(self) -> None:
        self._config = get_config().rag
        self._init()

    def _init(self) -> None:
        init_rag_db()

    # ---- 知识库 CRUD ----

    def create(
        self,
        name: str,
        description: str = "",
        embedding_model: Optional[str] = None,
        chunk_strategy: Optional[str] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ) -> KnowledgeBase:
        """创建知识库"""
        session = get_session()

        existing = session.query(KnowledgeBase).filter(KnowledgeBase.name == name).first()
        if existing:
            session.close()
            raise ValueError(f"知识库已存在: {name}")

        collection_name = f"kb:{name}"
        vs = VectorStore(persist_dir=self._config.chroma_persist_dir)
        vs.get_or_create_collection(collection_name)

        kb = KnowledgeBase(
            name=name,
            description=description,
            collection_name=collection_name,
            embedding_model=embedding_model or self._config.embedding_model,
            chunk_strategy=chunk_strategy or self._config.chunk_strategy,
            chunk_size=chunk_size or self._config.chunk_size,
            chunk_overlap=chunk_overlap or self._config.chunk_overlap,
        )
        session.add(kb)
        session.commit()
        session.refresh(kb)
        session.close()

        logger.info(f"知识库已创建: {name}")
        return kb

    def get(self, name: str) -> Optional[KnowledgeBase]:
        """获取知识库"""
        session = get_session()
        kb = session.query(KnowledgeBase).filter(KnowledgeBase.name == name).first()
        session.close()
        return kb

    def list_all(self) -> List[KnowledgeBase]:
        """列出所有知识库"""
        session = get_session()
        kbs = session.query(KnowledgeBase).all()
        session.close()
        return kbs

    def delete(self, name: str) -> bool:
        """删除知识库"""
        session = get_session()
        kb = session.query(KnowledgeBase).filter(KnowledgeBase.name == name).first()
        if not kb:
            session.close()
            return False

        # 删除 ChromaDB 集合
        try:
            vs = VectorStore(persist_dir=self._config.chroma_persist_dir)
            vs._client.delete_collection(name=kb.collection_name)
        except Exception as e:
            logger.warning(f"删除 ChromaDB 集合失败: {e}")

        session.delete(kb)
        session.commit()
        session.close()
        logger.info(f"知识库已删除: {name}")
        return True

    def get_stats(self, name: str) -> Dict[str, Any]:
        """知识库统计"""
        kb = self.get(name)
        if not kb:
            return {}
        return {
            "name": kb.name,
            "description": kb.description,
            "embedding_model": kb.embedding_model,
            "chunk_strategy": kb.chunk_strategy,
            "document_count": kb.document_count or 0,
            "chunk_count": kb.chunk_count or 0,
            "created_at": str(kb.created_at),
        }

    # ---- 文档摄取 ----

    def ingest_file(self, kb_name: str, file_path: str, tags: Optional[List[str]] = None) -> Document:
        """向知识库摄入文件"""
        kb = self.get(kb_name)
        if not kb:
            raise ValueError(f"知识库不存在: {kb_name}")
        pipeline = IngestionPipeline(kb)
        return pipeline.ingest_file(file_path, tags=tags)

    def ingest_directory(
        self, kb_name: str, directory: str, glob_pattern: str = "*.*", tags: Optional[List[str]] = None
    ) -> List[Document]:
        """向知识库摄入目录"""
        kb = self.get(kb_name)
        if not kb:
            raise ValueError(f"知识库不存在: {kb_name}")
        pipeline = IngestionPipeline(kb)
        return pipeline.ingest_directory(directory, glob_pattern, tags=tags)

    def ingest_text(
        self, kb_name: str, content: str, source: str = "manual", title: str = "text_input", tags: Optional[List[str]] = None
    ) -> Document:
        """向知识库摄入纯文本"""
        kb = self.get(kb_name)
        if not kb:
            raise ValueError(f"知识库不存在: {kb_name}")
        pipeline = IngestionPipeline(kb)
        return pipeline.ingest_text(content, source, title, tags)

    def ingest_url(self, kb_name: str, url: str, tags: Optional[List[str]] = None) -> Optional[Document]:
        """向知识库摄入 URL"""
        kb = self.get(kb_name)
        if not kb:
            raise ValueError(f"知识库不存在: {kb_name}")
        pipeline = IngestionPipeline(kb)
        return pipeline.ingest_url(url, tags)

    # ---- 检索 ----

    def search(
        self,
        kb_name: str,
        query: str,
        top_k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """搜索知识库"""
        kb = self.get(kb_name)
        if not kb:
            raise ValueError(f"知识库不存在: {kb_name}")

        retriever = HybridRetriever(kb)
        results = retriever.search(query, top_k=top_k)

        logger.info(f"检索 '{query}' → {len(results)} 条结果 (kb:{kb_name})")
        return results

    def search_all(self, query: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """跨所有知识库搜索"""
        all_results = []
        for kb in self.list_all():
            try:
                results = self.search(kb.name, query, top_k=top_k)
                all_results.extend(results)
            except Exception as e:
                logger.warning(f"搜索知识库 {kb.name} 失败: {e}")

        all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
        top_k = top_k or self._config.default_top_k
        return all_results[:top_k]

    # ---- 文档管理 ----

    def list_documents(self, kb_name: str) -> List[Dict[str, Any]]:
        """列出知识库中的文档"""
        kb = self.get(kb_name)
        if not kb:
            return []

        session = get_session()
        docs = session.query(Document).filter(Document.kb_id == kb.id).all()
        result = [
            {
                "id": d.id,
                "title": d.title,
                "source": d.source,
                "file_type": d.file_type,
                "chunk_count": d.chunk_count,
                "ingested_at": str(d.ingested_at),
            }
            for d in docs
        ]
        session.close()
        return result

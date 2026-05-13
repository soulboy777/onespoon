"""混合检索器 — ChromaDB 向量检索 + BM25 关键词检索"""

import math
from collections import defaultdict
from typing import Any, Dict, List

from loguru import logger
from rank_bm25 import BM25Okapi

from src.core.config import get_config
from src.rag.database import get_session
from src.rag.embedder import Embedder
from src.rag.models import Bm25Index, Chunk, KnowledgeBase
from src.rag.tokenizer import tokenize
from src.storage.vector_store import VectorStore


class HybridRetriever:
    """混合检索器 — 向量 + BM25"""

    def __init__(
        self,
        kb: KnowledgeBase,
        embedder: Embedder = None,
    ) -> None:
        self._kb = kb
        self._config = get_config().rag
        self._embedder = embedder or Embedder()

        self._vector_store = VectorStore(
            persist_dir=self._config.chroma_persist_dir
        )

    def search(
        self,
        query: str,
        top_k: int = None,
        alpha: float = None,
    ) -> List[Dict[str, Any]]:
        """混合检索"""
        top_k = top_k or self._config.default_top_k
        alpha = alpha if alpha is not None else self._config.hybrid_alpha
        vector_k = self._config.vector_top_k
        bm25_k = self._config.bm25_top_k

        # 1. 向量检索
        vector_results = self._vector_search(query, vector_k)

        # 2. BM25 关键词检索
        bm25_results = self._bm25_search(query, bm25_k)

        # 3. 融合排序
        fused = self._reciprocal_rank_fusion(
            vector_results, bm25_results, top_k, alpha
        )

        return fused

    def _vector_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """ChromaDB 向量检索"""
        try:
            results = self._vector_store.search(
                query=query,
                top_k=top_k,
                collection=self._kb.collection_name,
            )
            for r in results:
                r["source"] = "vector"
            return results
        except Exception as e:
            logger.warning(f"向量检索失败: {e}")
            return []

    def _bm25_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """BM25 关键词检索"""
        session = get_session()

        try:
            # 获取该知识库的所有 BM25 索引
            rows = (
                session.query(Bm25Index, Chunk)
                .join(Chunk, Bm25Index.chunk_id == Chunk.id)
                .filter(Bm25Index.kb_id == self._kb.id)
                .all()
            )

            if not rows:
                return []

            bm25_entry_list, chunk_list = zip(*rows) if rows else ([], [])

            tokenized_corpus = [
                entry.tokens.split() for entry in bm25_entry_list
            ]
            tokenized_query = tokenize(query)

            bm25 = BM25Okapi(tokenized_corpus)
            scores = bm25.get_scores(tokenized_query)

            scored = list(zip(scores, chunk_list))
            scored.sort(key=lambda x: -x[0])

            results = []
            for score, chunk in scored[:top_k]:
                if score > 0:
                    results.append({
                        "id": chunk.id,
                        "content": chunk.content,
                        "score": float(score),
                        "source": "bm25",
                        "metadata": {
                            "doc_id": chunk.doc_id,
                            "chunk_index": chunk.chunk_index,
                            "kb_name": self._kb.name,
                        },
                    })

            return results
        except Exception as e:
            logger.warning(f"BM25 检索失败: {e}")
            return []
        finally:
            session.close()

    def _reciprocal_rank_fusion(
        self,
        vector_results: List[Dict[str, Any]],
        bm25_results: List[Dict[str, Any]],
        top_k: int,
        alpha: float,
    ) -> List[Dict[str, Any]]:
        """RRF 融合排序"""
        k = 60  # RRF 常数

        fused_scores: Dict[str, float] = defaultdict(float)
        content_map: Dict[str, str] = {}
        metadata_map: Dict[str, dict] = {}

        # 向量得分
        for rank, item in enumerate(vector_results, 1):
            chunk_id = item.get("id", "")
            if not chunk_id:
                continue
            vector_score = alpha / (k + rank)
            fused_scores[chunk_id] += vector_score
            content_map[chunk_id] = item.get("content", "")
            metadata_map[chunk_id] = item.get("metadata", {})

        # BM25 得分
        for rank, item in enumerate(bm25_results, 1):
            chunk_id = item.get("id", "")
            if not chunk_id:
                continue
            bm25_weight = 1.0 - alpha
            bm25_score = bm25_weight / (k + rank)
            fused_scores[chunk_id] += bm25_score
            if chunk_id not in content_map:
                content_map[chunk_id] = item.get("content", "")
                metadata_map[chunk_id] = item.get("metadata", {})

        # 排序
        sorted_ids = sorted(fused_scores, key=fused_scores.get, reverse=True)[:top_k]

        results = []
        for chunk_id in sorted_ids:
            results.append({
                "id": chunk_id,
                "content": content_map.get(chunk_id, ""),
                "score": round(fused_scores[chunk_id], 6),
                "metadata": metadata_map.get(chunk_id, {}),
            })

        return results

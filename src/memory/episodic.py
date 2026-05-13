"""L3 — 情景/任务记忆（已完成任务的记录、决策过程、经验教训）"""

from typing import List, Optional

from loguru import logger

from src.memory.base import EpisodeFragment
from src.storage.vector_store import VectorStore


class EpisodicMemory:
    """L3 情景记忆 — 任务执行记录与经验"""

    def __init__(self, vector_store: Optional[VectorStore] = None) -> None:
        self._store = vector_store or VectorStore()
        self._collection_name = "episodic_memory"

    def add(self, episode: EpisodeFragment) -> str:
        """记录一次任务执行"""
        content = (
            f"任务: {episode.task}\n"
            f"结果: {episode.result}\n"
            f"步骤: {' → '.join(episode.steps)}\n"
            f"经验: {episode.lessons}"
        )

        metadata = {
            "success": episode.success,
            "task": episode.task,
            "lessons": episode.lessons,
        }

        doc_id = self._store.add(
            content=content,
            metadata=metadata,
            collection=self._collection_name,
        )
        logger.debug(f"情景记忆已记录: {episode.task}")
        return doc_id

    def search(self, query: str, top_k: int = 3) -> List[EpisodeFragment]:
        """检索相关历史任务"""
        results = self._store.search(
            query=query,
            top_k=top_k,
            collection=self._collection_name,
        )

        episodes = []
        for doc in results:
            meta = doc.get("metadata", {})
            episodes.append(EpisodeFragment(
                task=meta.get("task", ""),
                result=meta.get("result", doc["content"]),
                success=meta.get("success", True),
                steps=meta.get("steps", []),
                lessons=meta.get("lessons", ""),
            ))

        return episodes

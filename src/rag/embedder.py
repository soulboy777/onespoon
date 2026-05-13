"""嵌入模型适配器 — OpenAI / Ollama / 兼容接口"""

from typing import List, Optional

from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings
from loguru import logger

from src.core.config import get_config


class Embedder:
    """嵌入模型适配器"""

    def __init__(
        self,
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> None:
        config = get_config().rag
        self._provider = provider or config.embedding_provider
        self._model_name = model_name or config.embedding_model
        self._base_url = base_url or config.embedding_base_url
        self._embeddings: Optional[Embeddings] = None

    @property
    def embeddings(self) -> Embeddings:
        if self._embeddings is None:
            self._embeddings = self._create_embeddings()
        return self._embeddings

    def _create_embeddings(self) -> Embeddings:
        provider = self._provider.lower()

        if provider == "openai":
            logger.info(f"使用 OpenAI 嵌入: {self._model_name}")
            return OpenAIEmbeddings(model=self._model_name)

        elif provider == "openai_compatible":
            url = self._base_url or "https://api.openai.com/v1"
            logger.info(f"使用兼容接口嵌入: {self._model_name} @ {url}")
            return OpenAIEmbeddings(model=self._model_name, base_url=url)

        elif provider == "ollama":
            from langchain_community.embeddings import OllamaEmbeddings

            url = self._base_url or "http://localhost:11434"
            logger.info(f"使用 Ollama 嵌入: {self._model_name} @ {url}")
            return OllamaEmbeddings(model=self._model_name, base_url=url)

        else:
            raise ValueError(f"不支持的嵌入 provider: {provider}")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """批量嵌入"""
        if not texts:
            return []
        return self.embeddings.embed_documents(texts)

    def embed_query(self, query: str) -> List[float]:
        """单个查询嵌入"""
        return self.embeddings.embed_query(query)

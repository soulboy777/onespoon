"""文本分块器 — 支持 fixed / recursive / sentence 三种策略"""

import re
from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter
from loguru import logger

from src.core.config import get_config


class Chunker:
    """文本分块器"""

    def __init__(
        self,
        strategy: str = "recursive",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ) -> None:
        self._strategy = strategy
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    @classmethod
    def from_config(cls) -> "Chunker":
        config = get_config().rag
        return cls(
            strategy=config.chunk_strategy,
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
        )

    def split(self, text: str) -> List[str]:
        """分块入口"""
        if not text or not text.strip():
            return []

        if self._strategy == "fixed":
            return self._fixed_split(text)
        elif self._strategy == "recursive":
            return self._recursive_split(text)
        elif self._strategy == "sentence":
            return self._sentence_split(text)
        else:
            logger.warning(f"未知分块策略 '{self._strategy}'，降级为 recursive")
            return self._recursive_split(text)

    def _fixed_split(self, text: str) -> List[str]:
        """固定大小切分"""
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self._chunk_size,
            chunk_overlap=self._chunk_overlap,
            separators=["\n\n", "\n", "。", ".", "！", "？", "，", ",", " ", ""],
        )
        return splitter.split_text(text)

    def _recursive_split(self, text: str) -> List[str]:
        """递归分隔符切分"""
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self._chunk_size,
            chunk_overlap=self._chunk_overlap,
            separators=[
                "\n\n",
                "\n",
                "。",
                ". ",
                "！",
                "？",
                "；",
                "; ",
                "，",
                ", ",
                " ",
                "",
            ],
            keep_separator=True,
        )
        return splitter.split_text(text)

    def _sentence_split(self, text: str) -> List[str]:
        """按句子切分后合并到 chunk_size"""
        sentences = self._split_sentences(text)
        chunks: List[str] = []
        current_chunk = ""
        current_len = 0

        for sent in sentences:
            sent_len = len(sent)
            if current_len + sent_len > self._chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                overlap_text = current_chunk[-self._chunk_overlap:] if len(current_chunk) > self._chunk_overlap else current_chunk
                current_chunk = overlap_text + sent
                current_len = len(current_chunk)
            else:
                current_chunk += sent
                current_len += sent_len

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks if chunks else [text]

    def _split_sentences(self, text: str) -> List[str]:
        """分割句子（支持中英文）"""
        pattern = re.compile(
            r'(?<=[。！？.!?\n])\s*'
        )
        parts = pattern.split(text)

        sentences = []
        for p in parts:
            p = p.strip()
            if not p:
                continue
            for sub_p in re.split(r'(?<=[；;])\s*', p):
                sub_p = sub_p.strip()
                if sub_p:
                    sentences.append(sub_p)

        if not sentences:
            return [text]

        merged = []
        buffer = ""
        for sent in sentences:
            if len(buffer) + len(sent) < self._chunk_size:
                buffer += sent
            else:
                if buffer:
                    merged.append(buffer)
                buffer = sent
        if buffer:
            merged.append(buffer)

        return merged if merged else [text]

"""文档摄取管线 — Load → Parse → Chunk → Embed → Store"""

import json
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

from loguru import logger

from src.rag.chunker import Chunker
from src.rag.database import get_session
from src.rag.embedder import Embedder
from src.rag.models import Bm25Index, Chunk, Document, KnowledgeBase
from src.rag.tokenizer import tokenize


class IngestionPipeline:
    """文档摄取管线"""

    def __init__(self, kb: KnowledgeBase) -> None:
        self._kb = kb
        self._chunker = Chunker(
            strategy=kb.chunk_strategy,
            chunk_size=kb.chunk_size,
            chunk_overlap=kb.chunk_overlap,
        )
        self._embedder = Embedder()
        self._vector_store = None

    def _get_vector_store(self):
        if self._vector_store is None:
            from src.storage.vector_store import VectorStore
            from src.core.config import get_config

            self._vector_store = VectorStore(
                persist_dir=get_config().rag.chroma_persist_dir
            )
        return self._vector_store

    def ingest_file(self, file_path: str, tags: Optional[List[str]] = None) -> Document:
        """摄取单个文件"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        content = self._load_file(path)
        return self._ingest_text(
            content=content,
            source=str(path),
            title=path.stem,
            file_type=path.suffix.lower().lstrip("."),
            file_size=path.stat().st_size,
            tags=tags,
        )

    def ingest_directory(
        self,
        directory: str,
        glob_pattern: str = "*.*",
        tags: Optional[List[str]] = None,
    ) -> List[Document]:
        """摄取目录下所有文件"""
        dir_path = Path(directory)
        if not dir_path.exists():
            raise FileNotFoundError(f"目录不存在: {directory}")

        docs = []
        for file_path in dir_path.rglob(glob_pattern):
            if file_path.is_file():
                try:
                    doc = self.ingest_file(str(file_path), tags=tags)
                    docs.append(doc)
                except Exception as e:
                    logger.warning(f"摄取文件失败: {file_path} — {e}")

        return docs

    def ingest_url(self, url: str, tags: Optional[List[str]] = None) -> Optional[Document]:
        """摄取 URL"""
        try:
            import urllib.request

            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                content = resp.read().decode("utf-8", errors="replace")
        except Exception as e:
            logger.error(f"获取 URL 失败: {url} — {e}")
            return None

        parsed = urlparse(url)
        title = parsed.path.rstrip("/").split("/")[-1] or parsed.netloc
        return self._ingest_text(
            content=content,
            source=url,
            title=title,
            file_type="url",
            tags=tags,
        )

    def ingest_text(
        self,
        content: str,
        source: str = "manual",
        title: str = "text_input",
        tags: Optional[List[str]] = None,
    ) -> Document:
        """摄取纯文本"""
        return self._ingest_text(
            content=content,
            source=source,
            title=title,
            file_type="txt",
            tags=tags,
        )

    def _ingest_text(
        self,
        content: str,
        source: str,
        title: str,
        file_type: str = "unknown",
        file_size: int = 0,
        tags: Optional[List[str]] = None,
    ) -> Document:
        """核心摄取逻辑"""
        if not content or not content.strip():
            raise ValueError("内容为空")

        chunks_text = self._chunker.split(content)
        if not chunks_text:
            raise ValueError("分块结果为空")

        logger.info(
            f"摄取: {title} ({file_type}) → {len(chunks_text)} 个分块"
        )

        # 1. 创建文档记录
        session = get_session()
        doc = Document(
            kb_id=self._kb.id,
            source=source,
            title=title,
            file_type=file_type,
            file_size=file_size,
            chunk_count=len(chunks_text),
            tags=json.dumps(tags or [], ensure_ascii=False),
        )
        session.add(doc)
        session.flush()

        # 2. 批量嵌入
        try:
            embeddings = self._embedder.embed_documents(chunks_text)
        except Exception as e:
            logger.error(f"嵌入失败: {e}")
            session.rollback()
            raise

        # 3. 写入 ChromaDB + SQLite
        vs = self._get_vector_store()
        collection = self._kb.collection_name

        for i, (chunk_text, embedding) in enumerate(zip(chunks_text, embeddings)):
            import tiktoken

            enc = tiktoken.get_encoding("cl100k_base")
            token_count = len(enc.encode(chunk_text))

            embedding_id = vs.add(
                content=chunk_text,
                metadata={
                    "kb_id": self._kb.id,
                    "kb_name": self._kb.name,
                    "doc_id": doc.id,
                    "doc_title": title,
                    "source": source,
                    "chunk_index": i,
                },
                collection=collection,
            )

            chunk = Chunk(
                doc_id=doc.id,
                kb_id=self._kb.id,
                chunk_index=i,
                content=chunk_text,
                token_count=token_count,
                embedding_id=embedding_id,
                metadata_json=json.dumps(
                    {"source": source, "title": title}, ensure_ascii=False
                ),
            )
            session.add(chunk)
            session.flush()

            # BM25 索引
            tokens_str = " ".join(tokenize(chunk_text))
            bm25_entry = Bm25Index(
                chunk_id=chunk.id,
                tokens=tokens_str,
                kb_id=self._kb.id,
            )
            session.add(bm25_entry)

        # 4. 更新知识库计数
        self._kb.document_count = (self._kb.document_count or 0) + 1
        self._kb.chunk_count = (self._kb.chunk_count or 0) + len(chunks_text)
        session.commit()

        logger.info(f"文档已摄取: {title} ({len(chunks_text)} chunks)")
        return doc

    def _load_file(self, path: Path) -> str:
        """加载文件内容"""
        suffix = path.suffix.lower()

        if suffix in (".txt", ".md", ".py", ".js", ".ts", ".json", ".yaml", ".yml", ".html", ".css"):
            try:
                return path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                return path.read_text(encoding="gbk", errors="replace")

        elif suffix == ".docx":
            try:
                from docx import Document as DocxDoc

                doc = DocxDoc(str(path))
                return "\n".join(p.text for p in doc.paragraphs)
            except ImportError:
                raise ImportError("python-docx 未安装")

        elif suffix == ".pdf":
            try:
                from PyPDF2 import PdfReader

                reader = PdfReader(str(path))
                return "\n".join(
                    page.extract_text() or "" for page in reader.pages
                )
            except ImportError:
                raise ImportError("PyPDF2 未安装")

        else:
            try:
                return path.read_text(encoding="utf-8")
            except Exception:
                raise ValueError(f"不支持的文件格式: {suffix}")

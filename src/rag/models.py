"""RAG 数据模型 — 知识库、文档、分块"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, relationship


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_uuid() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class KnowledgeBase(Base):
    """知识库"""
    __tablename__ = "knowledge_bases"

    id = Column(String, primary_key=True, default=_new_uuid)
    name = Column(String(200), unique=True, nullable=False)
    description = Column(Text, default="")
    collection_name = Column(String(200), nullable=False, comment="ChromaDB 集合名")
    embedding_model = Column(String(100), default="openai")
    chunk_strategy = Column(String(50), default="recursive")
    chunk_size = Column(Integer, default=500)
    chunk_overlap = Column(Integer, default=50)
    document_count = Column(Integer, default=0)
    chunk_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    documents = relationship("Document", back_populates="knowledge_base", cascade="all, delete-orphan")
    chunks = relationship("Chunk", back_populates="knowledge_base", cascade="all, delete-orphan")


class Document(Base):
    """文档 — 一个文件/URL 的元数据"""
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=_new_uuid)
    kb_id = Column(String, ForeignKey("knowledge_bases.id"), nullable=False)
    source = Column(Text, nullable=False, comment="原始路径或 URL")
    title = Column(String(500), default="未命名文档")
    file_type = Column(String(50), default="unknown")
    file_size = Column(Integer, default=0)
    chunk_count = Column(Integer, default=0)
    tags = Column(Text, default="[]", comment="JSON 数组")
    metadata_json = Column(Text, default="{}", comment="额外元数据 JSON")
    ingested_at = Column(DateTime, default=_utcnow)

    knowledge_base = relationship("KnowledgeBase", back_populates="documents")
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")


class Chunk(Base):
    """文档分块"""
    __tablename__ = "chunks"

    id = Column(String, primary_key=True, default=_new_uuid)
    doc_id = Column(String, ForeignKey("documents.id"), nullable=False)
    kb_id = Column(String, ForeignKey("knowledge_bases.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    token_count = Column(Integer, default=0)
    embedding_id = Column(String, nullable=True, comment="ChromaDB 记录 ID")
    metadata_json = Column(Text, default="{}", comment="JSON: page, heading 等")

    document = relationship("Document", back_populates="chunks")
    knowledge_base = relationship("KnowledgeBase", back_populates="chunks")


class Bm25Index(Base):
    """BM25 关键词索引 — 存储分词后的 tokens"""
    __tablename__ = "bm25_index"

    chunk_id = Column(String, ForeignKey("chunks.id"), primary_key=True)
    tokens = Column(Text, nullable=False)
    kb_id = Column(String, ForeignKey("knowledge_bases.id"), nullable=False)

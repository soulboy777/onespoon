"""RAG 知识库 — 独立 SQLite 引擎 (data/knowledge.db)"""

import os
from pathlib import Path

from loguru import logger
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from src.core.config import get_config


_engine = None
_SessionLocal = None


def _ensure_db_dir() -> None:
    config = get_config()
    db_url = config.rag.database_url

    if db_url.startswith("sqlite:///"):
        db_path = db_url.replace("sqlite:///", "")
        if not os.path.isabs(db_path):
            project_root = Path(__file__).resolve().parent.parent.parent
            db_path = str(project_root / db_path)
        db_dir = os.path.dirname(db_path)
        os.makedirs(db_dir, exist_ok=True)


def get_engine():
    global _engine
    if _engine is None:
        _ensure_db_dir()
        config = get_config()
        db_url = config.rag.database_url
        _engine = create_engine(db_url, echo=False, connect_args={"check_same_thread": False})
        logger.info(f"RAG 数据库引擎已创建: {db_url}")
    return _engine


def get_session() -> Session:
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    return _SessionLocal()


def init_rag_db() -> None:
    """创建 RAG 表结构 + BM25 索引表"""
    from src.rag.models import Base

    engine = get_engine()
    Base.metadata.create_all(bind=engine)

    # 创建 BM25 关键词索引辅助表（存储分词后的内容，供 rank_bm25 使用）
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS bm25_index (
                chunk_id TEXT PRIMARY KEY,
                tokens TEXT NOT NULL,
                kb_id TEXT NOT NULL,
                FOREIGN KEY (chunk_id) REFERENCES chunks(id),
                FOREIGN KEY (kb_id) REFERENCES knowledge_bases(id)
            );
        """))
        conn.commit()

    logger.info("RAG 数据库表已初始化")


def reset_rag_db() -> None:
    """重置 RAG 数据库"""
    from src.rag.models import Base

    engine = get_engine()
    Base.metadata.drop_all(bind=engine)
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS bm25_index;"))
        conn.commit()
    Base.metadata.create_all(bind=engine)

    global _engine, _SessionLocal
    _engine = None
    _SessionLocal = None
    logger.warning("RAG 数据库已重置")

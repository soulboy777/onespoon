"""数据库引擎 — SQLAlchemy + SQLite"""

import os
from pathlib import Path

from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.core.config import get_config


_engine = None
_SessionLocal = None


def _ensure_db_dir() -> None:
    config = get_config()
    db_url = config.storage.database_url

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
        db_url = config.storage.database_url
        _engine = create_engine(db_url, echo=False, connect_args={"check_same_thread": False})
        logger.info(f"数据库引擎已创建: {db_url}")
    return _engine


def get_session() -> Session:
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    return _SessionLocal()


def init_db() -> None:
    """创建所有表"""
    from src.storage.models import Base

    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    logger.info("数据库表已初始化")


def reset_db() -> None:
    """删除并重建所有表（仅开发用）"""
    from src.storage.models import Base

    engine = get_engine()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    logger.warning("数据库已重置")

    global _engine, _SessionLocal
    _engine = None
    _SessionLocal = None

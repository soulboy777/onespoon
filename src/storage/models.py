"""数据库模型 — SQLAlchemy ORM"""

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


class Session(Base):
    """会话记录"""
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, default=_new_uuid)
    title = Column(String(500), default="新对话")
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")


class Message(Base):
    """对话消息"""
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=_new_uuid)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    token_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=_utcnow)

    session = relationship("Session", back_populates="messages")


class MemoryFragment(Base):
    """语义记忆片段"""
    __tablename__ = "memory_fragments"

    id = Column(String, primary_key=True, default=_new_uuid)
    type = Column(String(50), default="general")       # preference / fact / knowledge / decision
    content = Column(Text, nullable=False)
    importance = Column(Float, default=0.5)
    embedding_id = Column(String, nullable=True)        # ChromaDB 记录 ID
    created_at = Column(DateTime, default=_utcnow)
    last_accessed = Column(DateTime, default=_utcnow)


class Episode(Base):
    """情景记忆 — 已完成任务记录"""
    __tablename__ = "episodes"

    id = Column(String, primary_key=True, default=_new_uuid)
    task = Column(String(1000), nullable=False)
    result = Column(Text, default="")
    steps = Column(Text, default="[]")                   # JSON
    success = Column(Boolean, default=True)
    lessons = Column(Text, default="")
    embedding_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=_utcnow)


class ErrorLog(Base):
    """错误日志"""
    __tablename__ = "error_logs"

    id = Column(String, primary_key=True, default=_new_uuid)
    task_name = Column(String(500), nullable=False)
    error_type = Column(String(100), nullable=False)
    error_message = Column(Text, nullable=False)
    traceback = Column(Text, default="")
    context = Column(Text, default="")
    created_at = Column(DateTime, default=_utcnow)
    resolved = Column(Boolean, default=False)


class ScheduleItem(Base):
    """日程提醒"""
    __tablename__ = "schedule_items"

    id = Column(String, primary_key=True, default=_new_uuid)
    title = Column(String(500), nullable=False)
    description = Column(Text, default="")
    trigger_time = Column(DateTime, nullable=False)
    cron_expression = Column(String(100), nullable=True)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)

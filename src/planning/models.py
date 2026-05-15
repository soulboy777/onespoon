"""计划模块数据模型 — Plan + PlanStep"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, relationship


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_uuid() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class Plan(Base):
    """执行计划"""
    __tablename__ = "plans"

    id = Column(String, primary_key=True, default=_new_uuid)
    title = Column(String(500), nullable=False)
    description = Column(Text, default="")
    status = Column(String(20), default="draft")  # draft / ready / running / done / failed
    file_path = Column(String(500), default="")   # data/plans/xxx.md
    total_steps = Column(Integer, default=0)
    completed_steps = Column(Integer, default=0)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    executed_at = Column(DateTime, nullable=True)

    steps = relationship("PlanStep", back_populates="plan", cascade="all, delete-orphan",
                         order_by="PlanStep.index")


class PlanStep(Base):
    """计划步骤"""
    __tablename__ = "plan_steps"

    id = Column(String, primary_key=True, default=_new_uuid)
    plan_id = Column(String, ForeignKey("plans.id"), nullable=False)
    index = Column(Integer, nullable=False)
    name = Column(String(200), nullable=False)
    action = Column(Text, default="")
    target = Column(String(500), default="")
    expected = Column(Text, default="")
    depends_on = Column(String(200), default="")   # 依赖步骤 index，逗号分隔
    status = Column(String(20), default="pending")  # pending / running / done / failed / skipped
    error = Column(Text, default="")
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)

    plan = relationship("Plan", back_populates="steps")

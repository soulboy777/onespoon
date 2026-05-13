"""错误追踪 — 将任务失败记录写入 SQLite"""

import traceback
from typing import Any, Dict, Optional

from loguru import logger

from src.storage.database import get_session
from src.storage.models import ErrorLog


class ErrorTracker:
    """任务错误追踪器"""

    def __init__(self) -> None:
        self._errors: list = []

    def record_error(
        self,
        task_name: str,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """记录错误到数据库和内存"""
        error_type = type(error).__name__
        error_msg = str(error)
        tb = traceback.format_exc()

        logger.error(f"[{task_name}] {error_type}: {error_msg}")

        self._errors.append({
            "task": task_name,
            "type": error_type,
            "message": error_msg,
            "context": context,
        })

        try:
            session = get_session()
            log_entry = ErrorLog(
                task_name=task_name,
                error_type=error_type,
                error_message=error_msg,
                traceback=tb,
                context=str(context) if context else "",
            )
            session.add(log_entry)
            session.commit()
            return log_entry.id
        except Exception as e:
            logger.warning(f"错误日志写入数据库失败: {e}")
            return ""

    def get_recent_errors(self, limit: int = 20) -> list:
        try:
            session = get_session()
            entries = (
                session.query(ErrorLog)
                .order_by(ErrorLog.created_at.desc())
                .limit(limit)
                .all()
            )
            return [
                {
                    "id": e.id,
                    "task": e.task_name,
                    "type": e.error_type,
                    "message": e.error_message[:200],
                    "time": str(e.created_at),
                    "resolved": e.resolved,
                }
                for e in entries
            ]
        except Exception:
            return self._errors[-limit:]

    def mark_resolved(self, error_id: str) -> None:
        try:
            session = get_session()
            entry = session.query(ErrorLog).filter(ErrorLog.id == error_id).first()
            if entry:
                entry.resolved = True
                session.commit()
        except Exception as e:
            logger.warning(f"标记已解决失败: {e}")

    def summary(self) -> Dict[str, int]:
        """错误统计摘要"""
        try:
            session = get_session()
            total = session.query(ErrorLog).count()
            unresolved = session.query(ErrorLog).filter(ErrorLog.resolved == False).count()
            return {"total": total, "unresolved": unresolved}
        except Exception:
            return {"total": len(self._errors), "unresolved": len(self._errors)}

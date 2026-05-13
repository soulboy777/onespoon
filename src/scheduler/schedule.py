"""日程调度 — APScheduler 封装"""

from datetime import datetime
from typing import Callable, List, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from loguru import logger

from src.core.config import get_config


class ScheduleManager:
    """日程管理器"""

    def __init__(self) -> None:
        self._config = get_config()
        self._scheduler = BackgroundScheduler()
        self._jobs: dict = {}

    def start(self) -> None:
        if self._config.scheduler.enabled:
            self._scheduler.start()
            logger.info("日程调度已启动")

    def stop(self) -> None:
        self._scheduler.shutdown()
        logger.info("日程调度已停止")

    def add_reminder(
        self,
        title: str,
        trigger_time: datetime,
        callback: Optional[Callable] = None,
        description: str = "",
    ) -> str:
        """添加一次性提醒"""
        job = self._scheduler.add_job(
            func=callback or (lambda: logger.info(f"提醒: {title}")),
            trigger=DateTrigger(run_date=trigger_time),
            name=title,
        )
        self._jobs[job.id] = {
            "title": title,
            "trigger_time": trigger_time,
            "description": description,
        }
        logger.info(f"已添加提醒: {title} @ {trigger_time}")
        return job.id

    def add_cron_job(
        self,
        title: str,
        cron_expression: str,
        callback: Optional[Callable] = None,
        description: str = "",
    ) -> str:
        """添加周期性任务"""
        parts = cron_expression.strip().split()
        if len(parts) != 5:
            raise ValueError(f"cron 表达式格式错误: {cron_expression}")

        job = self._scheduler.add_job(
            func=callback or (lambda: logger.info(f"定时任务: {title}")),
            trigger=CronTrigger(
                minute=parts[0],
                hour=parts[1],
                day=parts[2],
                month=parts[3],
                day_of_week=parts[4],
            ),
            name=title,
        )
        self._jobs[job.id] = {
            "title": title,
            "cron": cron_expression,
            "description": description,
        }
        logger.info(f"已添加定时任务: {title} ({cron_expression})")
        return job.id

    def remove_job(self, job_id: str) -> bool:
        try:
            self._scheduler.remove_job(job_id)
            self._jobs.pop(job_id, None)
            return True
        except Exception:
            return False

    def list_jobs(self) -> List[dict]:
        return [
            {"id": j.id, "name": j.name, "next_run": str(j.next_run_time)}
            for j in self._scheduler.get_jobs()
        ]

    def get_job_count(self) -> int:
        return len(self._scheduler.get_jobs())

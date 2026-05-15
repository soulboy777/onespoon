"""计划管理器 — CRUD + 文件 I/O + 搜索"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

from src.core.config import get_config
from src.planning.models import Plan, PlanStep
from src.storage.database import get_engine, get_session


class PlanManager:
    """计划管理器"""

    def __init__(self) -> None:
        self._config = get_config().planning
        self._ensure_dir()

    def _ensure_dir(self) -> None:
        plans_dir = self._get_plans_dir()
        os.makedirs(plans_dir, exist_ok=True)

    def _get_project_root(self) -> Path:
        return Path(__file__).resolve().parent.parent.parent

    def _get_plans_dir(self) -> str:
        if os.path.isabs(self._config.plans_dir):
            return self._config.plans_dir
        return str(self._get_project_root() / self._config.plans_dir)

    def init_db(self) -> None:
        """创建 plans 表（如果不存在）"""
        engine = get_engine()
        Plan.metadata.create_all(bind=engine, tables=[Plan.__table__, PlanStep.__table__], checkfirst=True)

    # ---- CRUD ----

    def create_plan(
        self,
        title: str,
        description: str = "",
        steps: Optional[List[Dict[str, Any]]] = None,
    ) -> Plan:
        """创建计划"""
        self.init_db()
        session = get_session()

        plan = Plan(title=title, description=description, status="draft")
        session.add(plan)
        session.flush()

        if steps:
            for i, step_data in enumerate(steps, 1):
                step = PlanStep(
                    plan_id=plan.id,
                    index=i,
                    name=step_data.get("name", f"Step {i}"),
                    action=step_data.get("action", ""),
                    target=step_data.get("target", ""),
                    expected=step_data.get("expected", ""),
                    depends_on=step_data.get("depends_on", ""),
                )
                session.add(step)
            plan.total_steps = len(steps)

        session.commit()

        # 写入 Markdown 文件
        file_name = self._sanitize_filename(title) + ".md"
        file_path = os.path.join(self._get_plans_dir(), file_name)
        plan.file_path = file_path
        session.commit()

        self._write_markdown(plan)
        session.close()

        logger.info(f"计划已创建: {title} ({plan.total_steps} 步骤)")
        return plan

    def get_plan(self, plan_id: str) -> Optional[Plan]:
        self.init_db()
        session = get_session()
        plan = session.query(Plan).filter(Plan.id == plan_id).first()
        session.close()
        return plan

    def list_plans(self, status: Optional[str] = None) -> List[Plan]:
        self.init_db()
        session = get_session()
        query = session.query(Plan).order_by(Plan.created_at.desc())
        if status:
            query = query.filter(Plan.status == status)
        plans = query.all()
        session.close()
        return plans

    def update_plan(self, plan_id: str, **kwargs) -> Optional[Plan]:
        self.init_db()
        session = get_session()
        plan = session.query(Plan).filter(Plan.id == plan_id).first()
        if not plan:
            session.close()
            return None

        for key, val in kwargs.items():
            if hasattr(plan, key):
                setattr(plan, key, val)

        session.commit()
        session.refresh(plan)
        self._write_markdown(plan)
        session.close()
        return plan

    def delete_plan(self, plan_id: str) -> bool:
        self.init_db()
        session = get_session()
        plan = session.query(Plan).filter(Plan.id == plan_id).first()
        if not plan:
            session.close()
            return False

        if plan.file_path and os.path.exists(plan.file_path):
            os.remove(plan.file_path)

        session.delete(plan)
        session.commit()
        session.close()
        logger.info(f"计划已删除: {plan.title}")
        return True

    def add_step(self, plan_id: str, name: str, action: str = "", target: str = "", expected: str = "") -> Optional[PlanStep]:
        self.init_db()
        session = get_session()
        plan = session.query(Plan).filter(Plan.id == plan_id).first()
        if not plan:
            session.close()
            return None

        max_index = session.query(PlanStep).filter(PlanStep.plan_id == plan_id).count()
        step = PlanStep(
            plan_id=plan_id,
            index=max_index + 1,
            name=name,
            action=action,
            target=target,
            expected=expected,
        )
        session.add(step)
        plan.total_steps = max_index + 1
        session.commit()
        session.refresh(step)
        self._write_markdown(plan)
        session.close()
        return step

    def update_step_status(self, plan_id: str, step_index: int, status: str, error: str = "") -> bool:
        self.init_db()
        session = get_session()
        step = (
            session.query(PlanStep)
            .filter(PlanStep.plan_id == plan_id, PlanStep.index == step_index)
            .first()
        )
        if not step:
            session.close()
            return False

        step.status = status
        if status == "running":
            step.started_at = datetime.now(timezone.utc)
        elif status in ("done", "failed", "skipped"):
            step.finished_at = datetime.now(timezone.utc)
        if error:
            step.error = error

        # 更新计划完成计数
        plan = session.query(Plan).filter(Plan.id == plan_id).first()
        done_count = (
            session.query(PlanStep)
            .filter(PlanStep.plan_id == plan_id, PlanStep.status == "done")
            .count()
        )
        plan.completed_steps = done_count

        session.commit()
        self._write_markdown(plan)
        session.close()
        return True

    # ---- Markdown I/O ----

    def _write_markdown(self, plan: Plan) -> None:
        if not plan.file_path:
            return
        os.makedirs(os.path.dirname(plan.file_path), exist_ok=True)

        session = get_session()
        steps = (
            session.query(PlanStep)
            .filter(PlanStep.plan_id == plan.id)
            .order_by(PlanStep.index)
            .all()
        )
        session.close()

        status_icons = {"pending": "⏳", "running": "▶️", "done": "✅", "failed": "❌", "skipped": "⏭️"}

        lines = [
            f"# Plan: {plan.title}",
            "",
            f"**Status**: {plan.status}",
            f"**Created**: {plan.created_at}",
            f"**Steps**: {plan.completed_steps}/{plan.total_steps}",
            "",
            "## Goal",
            "",
            plan.description,
            "",
            "## Steps",
            "",
        ]

        for step in steps:
            icon = status_icons.get(step.status, "⏳")
            lines.append(f"### Step {step.index}: {step.name} {icon}")
            if step.action:
                lines.append(f"- **Action**: {step.action}")
            if step.target:
                lines.append(f"- **Target**: `{step.target}`")
            if step.expected:
                lines.append(f"- **Expected**: {step.expected}")
            if step.depends_on:
                lines.append(f"- **Depends on**: Step {step.depends_on}")
            if step.error:
                lines.append(f"- **Error**: {step.error}")
            lines.append("")

        with open(plan.file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def load_from_markdown(self, file_path: str) -> Optional[Plan]:
        """从 Markdown 文件恢复计划"""
        if not os.path.exists(file_path):
            return None

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        title = ""
        description = ""
        steps_data: List[Dict] = []

        current_section = ""
        current_step: Dict = {}

        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("# Plan:"):
                title = line.replace("# Plan:", "").strip()
            elif line.startswith("## Goal"):
                current_section = "goal"
            elif line.startswith("## Steps"):
                current_section = "steps"
            elif line.startswith("### Step"):
                if current_step:
                    steps_data.append(current_step)
                current_step = {"name": line.split(":", 1)[1].strip().split(" ")[0] if ":" in line else line}
                current_section = "step"
            elif current_section == "goal" and line and not line.startswith("**"):
                description += line + "\n"
            elif line.startswith("- **Action**:"):
                current_step["action"] = line.replace("- **Action**:", "").strip()
            elif line.startswith("- **Target**:"):
                current_step["target"] = line.replace("- **Target**:", "").strip()
            elif line.startswith("- **Expected**:"):
                current_step["expected"] = line.replace("- **Expected**:", "").strip()

        if current_step:
            steps_data.append(current_step)

        return self.create_plan(title=title, description=description.strip(), steps=steps_data)

    # ---- 工具 ----

    def _sanitize_filename(self, name: str) -> str:
        import re
        name = re.sub(r'[<>:"/\\|?*]', '-', name)
        return name.strip()[:100]

    def to_display_list(self, plans: List[Plan]) -> str:
        if not plans:
            return "暂无计划"

        status_icons = {"draft": "📝", "ready": "✅", "running": "▶️", "done": "✓", "failed": "✗"}
        lines = ["# 计划列表", ""]
        for i, p in enumerate(plans, 1):
            icon = status_icons.get(p.status, "⏳")
            lines.append(f"{i}. {icon} **{p.title}** [{p.status}] ({p.completed_steps}/{p.total_steps})")
            if p.description:
                lines.append(f"   {p.description[:80]}")
        return "\n".join(lines)

    def to_detail_string(self, plan: Plan) -> str:
        session = get_session()
        steps = (
            session.query(PlanStep)
            .filter(PlanStep.plan_id == plan.id)
            .order_by(PlanStep.index)
            .all()
        )
        session.close()

        status_icons = {"pending": "⏳", "running": "▶️", "done": "✅", "failed": "❌", "skipped": "⏭️"}
        lines = [
            f"# {plan.title}",
            f"Status: {plan.status} | Steps: {plan.completed_steps}/{plan.total_steps}",
            f"Created: {plan.created_at}",
            "",
            plan.description,
            "",
            "## Steps",
        ]
        for s in steps:
            icon = status_icons.get(s.status, "⏳")
            lines.append(f"\n### Step {s.index}: {s.name} {icon}")
            if s.action:
                lines.append(f"  Action: {s.action}")
            if s.target:
                lines.append(f"  Target: {s.target}")
            if s.expected:
                lines.append(f"  Expected: {s.expected}")
            if s.depends_on:
                lines.append(f"  Depends: Step {s.depends_on}")
            if s.error:
                lines.append(f"  ❌ Error: {s.error}")
        return "\n".join(lines)

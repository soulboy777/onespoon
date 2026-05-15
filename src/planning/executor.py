"""Execute Mode Agent — 按计划逐步执行"""

from typing import Any, Dict, List, Optional

from langchain.tools import BaseTool
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger

from src.planning.manager import PlanManager

EXECUTE_SYSTEM_PROMPT = """你是一个计划执行助手。按照给定的计划逐步执行。

## 原则:
1. 严格按计划步骤顺序执行
2. 每次只执行一个步骤
3. 执行前确认依赖步骤已完成
4. 每步执行后报告状态 (done / failed / skipped)
5. 步骤失败时记录错误信息并继续下一步

## 工具使用:
你可以使用所有可用工具来完成任务。

## 输出格式:
执行完每一步后，输出:
```
STEP_RESULT: <step_index> <status> <message>
```

完成所有步骤后输出:
```
PLAN_COMPLETE: <完成总结>
```
"""


class ExecuteModeAgent:
    """执行模式 Agent — 按计划逐步执行"""

    def __init__(self, llm: BaseChatModel, tools: List[BaseTool]) -> None:
        self._llm = llm
        self._tools = tools
        self._manager = PlanManager()
        self._active_plan_id: Optional[str] = None

    @property
    def active_plan(self) -> Optional[str]:
        return self._active_plan_id

    def execute_plan(self, plan_id: str) -> str:
        """执行指定计划"""
        plan = self._manager.get_plan(plan_id)
        if not plan:
            return f"计划不存在: {plan_id}"

        self._active_plan_id = plan_id
        self._manager.update_plan(plan_id, status="running")

        steps = self._get_steps(plan_id)
        if not steps:
            return "计划无步骤"

        log = [f"► 开始执行: **{plan.title}** ({len(steps)} 步骤)", ""]

        for step in steps:
            if step.depends_on:
                deps = [int(d.strip()) for d in step.depends_on.split(",") if d.strip()]
                for dep_idx in deps:
                    dep_step = self._get_step_by_index(plan_id, dep_idx)
                    if dep_step and dep_step.status != "done":
                        log.append(f"⚠ 跳过 Step {step.index}: 依赖 Step {dep_idx} 未完成")
                        self._manager.update_step_status(plan_id, step.index, "skipped", f"依赖未满足: Step {dep_idx}")
                        continue

            self._manager.update_step_status(plan_id, step.index, "running")

            try:
                messages = [
                    SystemMessage(content=EXECUTE_SYSTEM_PROMPT),
                    HumanMessage(content=f"""计划: {plan.title}

当前步骤:
- Step {step.index}/{len(steps)}: {step.name}
- Action: {step.action}
- Target: {step.target or '无'}
- Expected: {step.expected}

请执行这些操作并报告结果。

工具: {', '.join(t.name for t in self._tools)}"""),
                ]

                response = self._llm.invoke(messages)
                result_text = str(response.content)

                # 尝试解析执行结果
                if "failed" in result_text.lower() or "失败" in result_text or "错误" in result_text:
                    self._manager.update_step_status(plan_id, step.index, "failed", result_text[:200])
                    log.append(f"❌ Step {step.index}: {step.name} — 失败")
                else:
                    self._manager.update_step_status(plan_id, step.index, "done")
                    log.append(f"✓ Step {step.index}: {step.name} — 完成")

                log.append(f"  {result_text[:150]}")

            except Exception as e:
                self._manager.update_step_status(plan_id, step.index, "failed", str(e))
                log.append(f"❌ Step {step.index}: {step.name} — 异常: {e}")

        # 完成
        done = self._count_status(plan_id, "done")
        total = len(steps)
        if done == total:
            self._manager.update_plan(plan_id, status="done")
            log.append(f"\n✅ 计划执行完成! ({done}/{total})")
        elif done > 0:
            log.append(f"\n⚠ 计划部分完成: {done}/{total}")
        else:
            self._manager.update_plan(plan_id, status="failed")
            log.append(f"\n❌ 计划执行失败: 0/{total}")

        self._active_plan_id = None
        return "\n".join(log)

    def execute_single_step(self, plan_id: str, step_index: int) -> str:
        """执行单个步骤"""
        step = self._get_step_by_index(plan_id, step_index)
        if not step:
            return f"步骤不存在: Plan {plan_id}, Step {step_index}"

        self._manager.update_plan(plan_id, status="running")
        self._manager.update_step_status(plan_id, step_index, "running")

        plan = self._manager.get_plan(plan_id)
        try:
            messages = [
                SystemMessage(content=EXECUTE_SYSTEM_PROMPT),
                HumanMessage(content=f"""执行单个步骤:
- 计划: {plan.title if plan else ''}
- Step {step_index}: {step.name}
- Action: {step.action}
- Target: {step.target}
- Expected: {step.expected}

执行这些操作并报告结果。"""),
            ]
            response = self._llm.invoke(messages)
            result = str(response.content)
            self._manager.update_step_status(plan_id, step_index, "done")
            return f"✓ Step {step_index} 完成:\n{result[:300]}"
        except Exception as e:
            self._manager.update_step_status(plan_id, step_index, "failed", str(e))
            return f"❌ Step {step_index} 失败: {e}"

    def continue_plan(self, plan_id: str) -> str:
        """继续未完成的计划"""
        steps = self._get_steps(plan_id)
        pending = [s for s in steps if s.status in ("pending", "failed")]
        if not pending:
            plan = self._manager.get_plan(plan_id)
            return "计划已全部完成" if plan and plan.status == "done" else "无可执行的步骤"

        plan = self._manager.get_plan(plan_id)
        self._active_plan_id = plan_id
        self._manager.update_plan(plan_id, status="running")

        log = [f"► 继续执行: **{plan.title if plan else ''}** ({len(pending)} 待执行)", ""]

        for step in pending:
            self._manager.update_step_status(plan_id, step.index, "running")
            try:
                messages = [
                    SystemMessage(content=EXECUTE_SYSTEM_PROMPT),
                    HumanMessage(content=f"""步骤: {step.name}
Action: {step.action}
Target: {step.target}
Expected: {step.expected}"""),
                ]
                response = self._llm.invoke(messages)
                self._manager.update_step_status(plan_id, step.index, "done")
                log.append(f"✓ Step {step.index}: {step.name} — 完成")
            except Exception as e:
                self._manager.update_step_status(plan_id, step.index, "failed", str(e))
                log.append(f"❌ Step {step.index}: {step.name} — {e}")

        self._active_plan_id = None
        return "\n".join(log)

    def _get_steps(self, plan_id: str) -> list:
        from src.storage.database import get_session
        from src.planning.models import PlanStep

        session = get_session()
        steps = (
            session.query(PlanStep)
            .filter(PlanStep.plan_id == plan_id)
            .order_by(PlanStep.index)
            .all()
        )
        session.close()
        return steps

    def _get_step_by_index(self, plan_id: str, step_index: int):
        from src.storage.database import get_session
        from src.planning.models import PlanStep

        session = get_session()
        step = (
            session.query(PlanStep)
            .filter(PlanStep.plan_id == plan_id, PlanStep.index == step_index)
            .first()
        )
        session.close()
        return step

    def _count_status(self, plan_id: str, status: str) -> int:
        from src.storage.database import get_session
        from src.planning.models import PlanStep

        session = get_session()
        count = (
            session.query(PlanStep)
            .filter(PlanStep.plan_id == plan_id, PlanStep.status == status)
            .count()
        )
        session.close()
        return count

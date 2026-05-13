"""工作流编排 — 将复杂任务拆解为子任务并顺序执行"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from loguru import logger


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Task:
    """工作流中的单个任务"""

    id: str
    name: str
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    depends_on: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Workflow:
    """工作流 — 任务的有向无环图"""

    id: str
    name: str
    tasks: List[Task] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING

    def add_task(self, task: Task) -> None:
        self.tasks.append(task)

    def get_task(self, task_id: str) -> Optional[Task]:
        for t in self.tasks:
            if t.id == task_id:
                return t
        return None

    def get_ready_tasks(self) -> List[Task]:
        """获取所有依赖已满足的待执行任务"""
        ready = []
        for task in self.tasks:
            if task.status != TaskStatus.PENDING:
                continue
            if all(
                self.get_task(dep) and self.get_task(dep).status == TaskStatus.SUCCESS
                for dep in task.depends_on
            ):
                ready.append(task)
        return ready

    def is_complete(self) -> bool:
        return all(t.status in (TaskStatus.SUCCESS, TaskStatus.SKIPPED) for t in self.tasks)

    def is_failed(self) -> bool:
        return any(t.status == TaskStatus.FAILED for t in self.tasks)


class WorkflowEngine:
    """工作流执行引擎"""

    def __init__(self) -> None:
        self._executors: Dict[str, Callable] = {}

    def register_executor(self, task_type: str, executor: Callable) -> None:
        """注册任务执行器"""
        self._executors[task_type] = executor

    def execute(self, workflow: Workflow) -> Workflow:
        """执行工作流"""
        workflow.status = TaskStatus.RUNNING
        logger.info(f"开始执行工作流: {workflow.name}")

        max_iterations = len(workflow.tasks) * 3
        iteration = 0

        while not workflow.is_complete() and iteration < max_iterations:
            iteration += 1
            ready_tasks = workflow.get_ready_tasks()

            if not ready_tasks:
                if all(t.status in (TaskStatus.FAILED, TaskStatus.SUCCESS, TaskStatus.SKIPPED)
                       for t in workflow.tasks):
                    break
                logger.warning("存在无法执行的任务（依赖未满足）")
                break

            for task in ready_tasks:
                self._execute_task(task)

        if workflow.is_complete():
            workflow.status = TaskStatus.SUCCESS
            logger.info(f"工作流完成: {workflow.name}")
        elif workflow.is_failed():
            workflow.status = TaskStatus.FAILED
            logger.error(f"工作流失败: {workflow.name}")
        else:
            workflow.status = TaskStatus.FAILED
            logger.warning(f"工作流部分完成: {workflow.name}")

        return workflow

    def _execute_task(self, task: Task) -> None:
        task.status = TaskStatus.RUNNING
        logger.info(f"执行任务: {task.name}")

        try:
            executor = self._executors.get(task.name.split(":")[0] if ":" in task.name else task.name)
            if executor:
                task.result = executor(task)
            else:
                task.result = f"任务 {task.name} 无对应执行器"
            task.status = TaskStatus.SUCCESS
            logger.info(f"任务完成: {task.name}")
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            logger.error(f"任务失败: {task.name} — {e}")


def decompose_task(goal: str, llm=None) -> Workflow:
    """将自然语言目标拆解为工作流（简化版，Phase 3 接入 LLM 智能拆解）"""
    workflow = Workflow(id="auto", name=goal)

    steps = goal.split("然后")
    for i, step in enumerate(steps):
        task = Task(
            id=f"step_{i+1}",
            name=step.strip(),
            description=step.strip(),
        )
        if i > 0:
            task.depends_on = [f"step_{i}"]
        workflow.add_task(task)

    return workflow

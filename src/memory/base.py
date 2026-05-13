"""记忆系统容器"""

from typing import Dict, List, Optional


class MemoryFragment:
    """语义记忆片段"""

    def __init__(self, content: str, importance: float = 0.5, metadata: Optional[Dict] = None) -> None:
        self.content = content
        self.importance = importance
        self.metadata = metadata or {}

    def to_dict(self) -> dict:
        return {"content": self.content, "importance": self.importance, "metadata": self.metadata}


class EpisodeFragment:
    """情景记忆片段"""

    def __init__(self, task: str, result: str, success: bool, steps: List[str], lessons: str = "") -> None:
        self.task = task
        self.result = result
        self.success = success
        self.steps = steps
        self.lessons = lessons

    def to_dict(self) -> dict:
        return {
            "task": self.task,
            "result": self.result,
            "success": self.success,
            "steps": self.steps,
            "lessons": self.lessons,
        }

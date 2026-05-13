"""工具基类 — LangChain BaseTool 封装"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type

from langchain.tools import BaseTool as LangChainBaseTool
from pydantic import BaseModel, Field


class ToolInput(BaseModel):
    """工具输入基类"""
    pass


class BaseTool(LangChainBaseTool, ABC):
    """工具基类 — 扩展 LangChain BaseTool"""

    category: str = "general"
    requires_confirmation: bool = False

    @abstractmethod
    def _run(self, **kwargs) -> str:
        """同步执行"""
        ...

    async def _arun(self, **kwargs) -> str:
        """异步执行"""
        return self._run(**kwargs)


class ToolRegistry:
    """工具注册中心"""

    _instance: Optional["ToolRegistry"] = None

    def __init__(self) -> None:
        self._tools: Dict[str, BaseTool] = {}

    @classmethod
    def get_instance(cls) -> "ToolRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(self, tool: BaseTool) -> None:
        """注册工具"""
        self._tools[tool.name] = tool

    def register_many(self, tools: List[BaseTool]) -> None:
        """批量注册"""
        for tool in tools:
            self.register(tool)

    def get(self, name: str) -> Optional[BaseTool]:
        """按名称获取工具"""
        return self._tools.get(name)

    def list_all(self) -> List[BaseTool]:
        """列出所有工具"""
        return list(self._tools.values())

    def list_by_category(self, category: str) -> List[BaseTool]:
        """按类别筛选"""
        return [t for t in self._tools.values() if t.category == category]

    def categories(self) -> List[str]:
        """列出所有类别"""
        return list({t.category for t in self._tools.values()})

    def unregister(self, name: str) -> None:
        """移除工具"""
        self._tools.pop(name, None)

    def clear(self) -> None:
        """清空注册"""
        self._tools.clear()

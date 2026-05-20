"""工具基类 — LangChain BaseTool 封装 + JSON 输出包装"""

import json
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from langchain.tools import BaseTool as LangChainBaseTool
from pydantic import BaseModel, Field


class ToolInput(BaseModel):
    """工具输入基类"""
    pass


class BaseTool(LangChainBaseTool, ABC):
    """工具基类 — 扩展 LangChain BaseTool"""

    category: str = "general"
    requires_confirmation: bool = False
    is_readonly: bool = True

    def _run(self, **kwargs) -> str:
        """LangChain 调用入口，自动包装 JSON 输出"""
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        try:
            result = self._execute(**kwargs)
            if isinstance(result, dict):
                result.setdefault("status", "success")
                result.setdefault("timestamp", ts)
                return json.dumps(result, ensure_ascii=False)
            elif isinstance(result, str):
                return json.dumps(
                    {"status": "success", "data": result, "timestamp": ts},
                    ensure_ascii=False,
                )
            else:
                return json.dumps(
                    {"status": "success", "data": str(result), "timestamp": ts},
                    ensure_ascii=False,
                )
        except Exception as e:
            import traceback

            return json.dumps(
                {
                    "status": "error",
                    "error": str(e),
                    "traceback": traceback.format_exc(limit=2),
                    "timestamp": ts,
                },
                ensure_ascii=False,
            )

    def _execute(self, **kwargs) -> Dict[str, Any]:
        """子类覆写此方法，返回 dict"""
        raise NotImplementedError(
            f"Tool '{self.name}': 请覆写 _execute() 方法并返回 dict"
        )

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
        self._tools[tool.name] = tool

    def register_many(self, tools: List[BaseTool]) -> None:
        for tool in tools:
            self.register(tool)

    def get(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def list_all(self) -> List[BaseTool]:
        return list(self._tools.values())

    def list_by_category(self, category: str) -> List[BaseTool]:
        return [t for t in self._tools.values() if t.category == category]

    def categories(self) -> List[str]:
        return list({t.category for t in self._tools.values()})

    def unregister(self, name: str) -> None:
        self._tools.pop(name, None)

    def clear(self) -> None:
        self._tools.clear()

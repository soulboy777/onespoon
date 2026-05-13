"""工具注册中心入口 — 创建默认工具集"""

from typing import List, Optional

from src.tools.base import BaseTool, ToolRegistry
from src.tools.file_ops import (
    DeleteFileTool,
    ListDirTool,
    MoveFileTool,
    ReadFileTool,
    WriteFileTool,
)
from src.tools.memory_tool import MemoryQueryTool
from src.tools.note import NoteTool
from src.tools.rag_tool import RAGListKBTool, RAGSearchTool
from src.tools.shell_exec import ShellExecTool
from src.tools.web_search import WebSearchTool


def create_default_tools() -> List[BaseTool]:
    """创建默认工具集"""
    return [
        ReadFileTool(),
        WriteFileTool(),
        ListDirTool(),
        MoveFileTool(),
        DeleteFileTool(),
        ShellExecTool(),
        WebSearchTool(),
        NoteTool(),
        MemoryQueryTool(),
        RAGSearchTool(),
        RAGListKBTool(),
    ]


def create_default_tools_with_rag(kb_manager) -> List[BaseTool]:
    """创建工具集并注入 RAG 管理器"""
    tools = create_default_tools()
    for tool in tools:
        if hasattr(tool, "set_manager") and tool.category == "rag":
            tool.set_manager(kb_manager)
        if hasattr(tool, "set_memory_manager") and tool.category == "memory":
            from src.memory.manager import MemoryManager
            if kb_manager and hasattr(tool, "_memory_manager"):
                pass
    return tools


def register_default_tools(registry: Optional[ToolRegistry] = None) -> ToolRegistry:
    """注册默认工具集"""
    if registry is None:
        registry = ToolRegistry.get_instance()
    registry.register_many(create_default_tools())
    return registry

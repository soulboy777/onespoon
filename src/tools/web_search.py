"""网络搜索工具"""

from typing import Optional

from pydantic import BaseModel, Field

from src.tools.base import BaseTool


class WebSearchInput(BaseModel):
    query: str = Field(description="搜索关键词")


class WebSearchTool(BaseTool):
    name: str = "web_search"
    description: str = "搜索网络获取信息。参数: query (搜索关键词)"
    args_schema: type[BaseModel] = WebSearchInput
    category: str = "web"

    def _run(self, query: str) -> str:
        # Phase 1: 占位实现，Phase 2 接入真实搜索 API
        return (
            f"网络搜索功能待接入。查询: {query}\n"
            "提示: 在 config 中配置 SERPAPI_API_KEY 或 TAVILY_API_KEY 后启用真实搜索。"
        )

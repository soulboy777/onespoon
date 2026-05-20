"""网络搜索工具"""

from pydantic import BaseModel, Field

from src.tools.base import BaseTool


class WebSearchInput(BaseModel):
    query: str = Field(description="搜索关键词")


class WebSearchTool(BaseTool):
    name: str = "web_search"
    description: str = "搜索网络获取信息。参数: query (搜索关键词)"
    args_schema: type[BaseModel] = WebSearchInput
    category: str = "web"

    def _execute(self, query: str) -> dict:
        return {
            "data": f"网络搜索功能待接入。查询: {query}",
            "query": query,
            "action": "search",
            "note": "配置 SERPAPI_API_KEY 或 TAVILY_API_KEY 启用",
        }

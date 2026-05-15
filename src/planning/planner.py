"""Plan Mode Agent — 只读工具集，生成结构化计划"""

from typing import Any, Dict, List, Optional

from langchain.tools import BaseTool
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger

from src.planning.manager import PlanManager
from src.planning.template import PlanTemplate

PLAN_SYSTEM_PROMPT = """你是一个计划生成助手。你的任务是根据用户描述生成结构化的执行计划。

## 你的能力（只读）:
- 浏览文件结构 (read_file, list_dir)
- 搜索信息 (web_search)
- 查询记忆和知识库

## 你不能:
- 创建、修改或删除任何文件
- 执行任何 shell 命令

## 输出要求:
分析用户需求后，输出一个结构化的计划，包含以下部分：

1. **Goal (目标)**: 一句话描述要做什么
2. **Steps (步骤)**: 每个步骤包含:
   - name: 简短名称
   - action: 具体要做什么
   - target: 目标文件/目录 (可选)
   - expected: 预期结果
   - depends_on: 依赖的上一步序号 (可选)
3. **Affected Files**: 可能涉及的文件
4. **Notes**: 注意事项

请用 JSON 格式输出:
```json
{{
  "title": "计划标题",
  "description": "目标描述",
  "steps": [
    {{"name": "步骤名", "action": "行动", "target": "路径", "expected": "预期", "depends_on": ""}},
    ...
  ],
  "affected_files": ["文件1", "文件2"],
  "notes": "注意事项"
}}
```

只输出 JSON，不要多余文字。
"""


class PlanModeAgent:
    """计划模式 Agent — 只读工具"""

    def __init__(self, llm: BaseChatModel, tools: List[BaseTool]) -> None:
        self._llm = llm
        self._all_tools = tools
        self._readonly_tools = [t for t in tools if getattr(t, "is_readonly", True)]
        self._manager = PlanManager()
        self._template = PlanTemplate()

    def generate_plan(self, user_input: str) -> str:
        """根据用户输入生成计划"""
        readonly_names = [t.name for t in self._readonly_tools]

        messages = [
            SystemMessage(content=PLAN_SYSTEM_PROMPT),
            HumanMessage(content=f"""用户需求: {user_input}

可用的只读工具: {', '.join(readonly_names)}

请分析并输出 JSON 计划。"""),
        ]

        try:
            response = self._llm.invoke(messages)
            content = str(response.content)

            import json
            import re

            json_match = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(1))
            else:
                json_match = re.search(r"\{.*\}", content, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group(0))
                else:
                    return f"无法解析计划，原始输出:\n{content}"

            plan = self._manager.create_plan(
                title=data.get("title", "未命名计划"),
                description=data.get("description", ""),
                steps=data.get("steps", []),
            )

            return (
                f"✓ 计划已创建: #{plan.id[:8]} **{plan.title}**\n"
                f"  步骤数: {plan.total_steps}\n"
                f"  存储于: {plan.file_path}\n\n"
                + self._manager.to_detail_string(plan)
            )

        except json.JSONDecodeError as e:
            return f"计划生成失败 (JSON解析错误): {e}"
        except Exception as e:
            logger.error(f"计划生成失败: {e}")
            return f"计划生成失败: {e}"

    def refine_plan(self, plan_id: str, instruction: str) -> str:
        """修改已有计划"""
        plan = self._manager.get_plan(plan_id)
        if not plan:
            return f"计划不存在: {plan_id}"

        messages = [
            SystemMessage(content=PLAN_SYSTEM_PROMPT),
            HumanMessage(content=f"""已有计划:
{self._manager.to_detail_string(plan)}

修改指令: {instruction}

请输出修改后的计划 JSON（保持原有步骤编号，只修改需要改的部分）。"""),
        ]

        try:
            response = self._llm.invoke(messages)
            content = str(response.content)

            import json
            import re

            json_match = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(1))

                if data.get("title"):
                    self._manager.update_plan(plan_id, title=data["title"])
                if data.get("description"):
                    self._manager.update_plan(plan_id, description=data["description"])

                for step_data in data.get("steps", []):
                    idx = step_data.get("index", 0)
                    if idx:
                        self._manager.update_step_status(
                            plan_id, idx, "pending", ""
                        )

                return "✓ 计划已更新"
            else:
                return f"无法解析响应: {content[:200]}"
        except Exception as e:
            return f"计划更新失败: {e}"

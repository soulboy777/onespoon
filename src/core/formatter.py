"""五层格式化引擎 — LLM 输入/输出结构化管理"""

import json
import re
from datetime import datetime
from typing import Any, Dict, List

from langchain.tools import BaseTool as LangChainBaseTool


FORMAT_INSTRUCTION = """
### 回答格式要求（必须严格遵守）

你的 Final Answer 必须严格分为两段，不写标记的回复视为格式错误：

【回】用活泼好动的小朋友语气说话，一句话说清结果。
     语气词用：嘞(肯定轻松)、嘿(带劲利索)、嘻(俏皮带笑)、吁(松口气)。
     不用：啦、呀、哦、呢。
     控制在15字以内，要简洁。
     示例："写好嘞！" "找到嘿~" "弄完了嘻" "放进去了吁"

【细】详细说明操作内容，格式严格为：
     时间 | 文件路径 | 做了什么操作
     示例：【细】14:30 | D:\\test\\foo.py | 第19行添加了导入
"""


def build_tools_schema(tools: List[LangChainBaseTool]) -> str:
    """将工具列表转为 JSON Schema 描述，嵌入系统提示词"""
    schemas = []
    for tool in tools:
        schema = {
            "name": tool.name,
            "description": tool.description,
        }
        if hasattr(tool, "args_schema") and tool.args_schema:
            try:
                schema["input"] = tool.args_schema.model_json_schema()
            except Exception:
                schema["input"] = {}
        schemas.append(schema)

    return json.dumps(schemas, ensure_ascii=False, indent=2)


def parse_response(text: str) -> Dict[str, str]:
    """拆分 LLM 输出为 main(主句) + sub(副句)"""
    if not text:
        return {"main": "", "sub": ""}

    # 匹配【回】...【细】... 或 【回】...(结尾)
    main_match = re.search(r"【回】\s*(.*?)(?:【细】|$)", text, re.DOTALL)
    sub_match = re.search(r"【细】\s*(.*?)$", text, re.DOTALL)

    main = main_match.group(1).strip() if main_match else ""
    sub = sub_match.group(1).strip() if sub_match else ""

    # 如果没匹配到【回】，但有内容，把全文当主句
    if not main and not sub and text.strip():
        main = text.strip()

    return {"main": main, "sub": sub}


def build_structured_prompt(
    agent_name: str,
    tools: List[LangChainBaseTool],
    context_memory: str,
    current_time: str = "",
    format_instruction: str = "",
) -> str:
    """构建结构化系统提示词"""
    if not current_time:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")

    tools_schema = build_tools_schema(tools)
    tool_names = ", ".join(t.name for t in tools)
    fmt = format_instruction or FORMAT_INSTRUCTION

    prompt = f"""【角色】你是 {agent_name}，一个桌面 AI 智能助手。

【能力】你可以使用以下工具（JSON Schema 格式）：

{tools_schema}

【工具名称】{tool_names}

【工作流】严格按以下格式思考并执行：

Thought: 我需要做什么？
Action: 工具名
Action Input: {{"key":"value"}}  ← 必须是合法 JSON
Observation: 工具返回结果
... (可重复 Thought/Action/Action Input/Observation)
Final Answer: 最终回答（必须遵守【输出格式】）

{fmt}

【时间】当前: {current_time}

【记忆】{context_memory}

Question: {{input}}
{{agent_scratchpad}}"""

    return prompt

"""ReAct Agent 主循环 — 集成记忆、压缩、工具调度"""

from typing import Any, Dict, List, Optional

from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import BaseTool
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from loguru import logger

from src.compression.compressor import ContextCompressor
from src.core.config import get_config
from src.memory.manager import MemoryManager

REACT_SYSTEM_PROMPT = """你是 {agent_name}，一个桌面 AI 智能助手。

你有以下能力：
- 读写文件、执行命令
- 搜索网络获取信息
- 记忆和回顾之前对话中的重要信息
- 管理文档分类

请遵循以下原则：
1. 可用工具解决问题时，必须使用工具
2. 每次只调用一个工具，观察结果再决定下一步
3. 回答要简洁直接
4. 遇到不确定的情况，诚实说明

你可以使用的工具: {tools}

使用格式：
Thought: 思考下一步该做什么
Action: 工具名称
Action Input: 工具输入
Observation: 工具返回结果
... (可重复)
Final Answer: 最终回答用户

当前时间: {current_time}
"""

SYSTEM_TEMPLATE = """你是 {agent_name}，一个桌面 AI 智能助手。

你可以使用的工具: {tools}

工具名称列表: {tool_names}

使用以下格式来解决问题：
Thought: 我应该怎么做？
Action: 工具名称
Action Input: 工具输入参数
Observation: 工具执行结果
... (可重复 Thought/Action/Action Input/Observation)
Final Answer: 最终回答

{context_memory}

Question: {input}
{agent_scratchpad}"""


class Agent:
    """ReAct Agent — 核心智能体引擎"""

    MODE_PLAN = "plan"
    MODE_EXECUTE = "execute"

    def __init__(
        self,
        llm: BaseChatModel,
        tools: List[BaseTool],
        memory_manager: Optional[MemoryManager] = None,
        compressor: Optional[ContextCompressor] = None,
        mode: str = "execute",
    ) -> None:
        self._config = get_config()
        self._llm = llm
        self._all_tools = tools
        self._mode = mode
        self._memory = memory_manager or MemoryManager()
        self._compressor = compressor or ContextCompressor(llm)

        self._tool_map = {t.name: t for t in tools}
        self._update_executor()

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def tools(self) -> List[BaseTool]:
        return self._all_tools

    @property
    def active_tools(self) -> List[BaseTool]:
        """当前模式下的可用工具"""
        if self._mode == self.MODE_PLAN:
            return [t for t in self._all_tools if getattr(t, "is_readonly", True)]
        return self._all_tools

    def set_mode(self, mode: str) -> str:
        """切换模式"""
        if mode not in (self.MODE_PLAN, self.MODE_EXECUTE):
            raise ValueError(f"无效模式: {mode}，可选 plan / execute")
        self._mode = mode
        self._update_executor()
        readonly_count = len([t for t in self._all_tools if getattr(t, "is_readonly", True)])
        total = len(self._all_tools)
        logger.info(f"Agent 模式切换: {mode} ({readonly_count}/{total} 只读工具)")
        return self._mode

    def _update_executor(self) -> None:
        active = self.active_tools

        self._prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_TEMPLATE),
                MessagesPlaceholder(variable_name="chat_history", optional=True),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        self._agent = create_react_agent(
            llm=self._llm,
            tools=active,
            prompt=self._prompt,
        )

        self._executor = AgentExecutor(
            agent=self._agent,
            tools=active,
            verbose=self._config.agent.verbose,
            max_iterations=self._config.agent.max_iterations,
            handle_parsing_errors=True,
            return_intermediate_steps=True,
        )

    @property
    def tools(self) -> List[BaseTool]:
        return self._all_tools

    @property
    def memory(self) -> MemoryManager:
        return self._memory

    def run(self, user_input: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """执行一次 Agent 对话"""
        logger.info(f"Agent [{self._mode}] 收到输入: {user_input[:100]}...")

        # 1. 获取语义记忆
        semantic_memories = self._memory.retrieve_semantic(user_input)
        episodic_memories = self._memory.retrieve_episodic(user_input)

        # 2. 组装上下文字符串
        context_memory = self._memory.build_context_string(
            semantic_memories, episodic_memories
        )

        # 3. 压缩上下文
        active_tools = self.active_tools
        tool_names = ", ".join([t.name for t in active_tools])
        tools_desc = "\n".join([f"- {t.name}: {t.description}" for t in active_tools])

        system_content = SYSTEM_TEMPLATE.format(
            agent_name=self._config.agent.name,
            tools=tools_desc,
            tool_names=tool_names,
            context_memory=context_memory,
            input=user_input,
            agent_scratchpad="",
        )

        compressed_system = self._compressor.compress(system_content)

        # 4. 执行 Agent
        try:
            result = self._executor.invoke(
                {
                    "input": user_input,
                    "tools": tools_desc,
                    "tool_names": tool_names,
                    "context_memory": context_memory,
                    "chat_history": [],
                    "agent_scratchpad": "",
                }
            )
        except Exception as e:
            logger.error(f"Agent 执行失败: {e}")
            return {"output": f"执行出错: {e}", "intermediate_steps": []}

        # 5. 写入记忆
        output = result.get("output", "")
        self._memory.add_to_buffer(HumanMessage(content=user_input))
        self._memory.add_to_buffer(AIMessage(content=output))

        # 评估重要性，写入语义记忆
        importance = self._memory.evaluate_importance(user_input, output)
        if importance >= self._config.memory.importance_threshold:
            self._memory.add_semantic(
                content=f"用户: {user_input}\n助手: {output}",
                importance=importance,
            )

        return result

    async def arun(
        self, user_input: str, session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """异步执行"""
        return self.run(user_input, session_id)

"""ReAct Agent 主循环 — 集成记忆、压缩、工具调度、格式化输出"""

from typing import Any, Dict, List, Optional

from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import BaseTool
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from loguru import logger

from src.compression.compressor import ContextCompressor
from src.core.config import get_config
from src.core.formatter import build_structured_prompt, parse_response
from src.memory.manager import MemoryManager


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
        if self._mode == self.MODE_PLAN:
            return [t for t in self._all_tools if getattr(t, "is_readonly", True)]
        return self._all_tools

    def set_mode(self, mode: str) -> str:
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

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "{system_prompt}"),
                MessagesPlaceholder(variable_name="chat_history", optional=True),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        self._agent = create_react_agent(
            llm=self._llm,
            tools=active,
            prompt=prompt,
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
        logger.info(f"Agent [{self._mode}] 收到输入: {user_input[:100]}...")

        # 1. 获取语义记忆
        semantic_memories = self._memory.retrieve_semantic(user_input)
        episodic_memories = self._memory.retrieve_episodic(user_input)

        # 2. 组装上下文
        context_memory = self._memory.build_context_string(
            semantic_memories, episodic_memories
        )

        # 3. 构建结构化 prompt
        import datetime
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        active_tools = self.active_tools

        system_prompt = build_structured_prompt(
            agent_name=self._config.agent.name,
            tools=active_tools,
            context_memory=context_memory,
            current_time=current_time,
        )

        # 4. 压缩
        compressed_prompt = self._compressor.compress(system_prompt)

        # 5. 执行 Agent
        try:
            result = self._executor.invoke(
                {
                    "system_prompt": compressed_prompt,
                    "input": user_input,
                    "chat_history": [],
                    "agent_scratchpad": "",
                }
            )
        except Exception as e:
            logger.error(f"Agent 执行失败: {e}")
            return {"output": f"执行出错: {e}", "main": "", "sub": "", "intermediate_steps": []}

        # 6. 解析输出
        raw_output = result.get("output", "")
        parsed = parse_response(raw_output)
        main_text = parsed["main"]
        sub_text = parsed["sub"]

        # 7. 写入记忆
        self._memory.add_to_buffer(HumanMessage(content=user_input))
        self._memory.add_to_buffer(AIMessage(content=raw_output))

        importance = self._memory.evaluate_importance(user_input, raw_output)
        if importance >= self._config.memory.importance_threshold:
            self._memory.add_semantic(
                content=f"用户: {user_input}\n主: {main_text}\n细: {sub_text}",
                importance=importance,
            )

        return {
            "output": raw_output,
            "main": main_text,
            "sub": sub_text,
            "intermediate_steps": result.get("intermediate_steps", []),
        }

    async def arun(self, user_input: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        return self.run(user_input, session_id)

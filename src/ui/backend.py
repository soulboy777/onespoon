"""UI ↔ Agent 桥接层 — Signals/Slots 双向通信"""

import os
import sys
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot, Property
from loguru import logger

from src.core.config import get_config, load_config
from src.core.llm import get_llm
from src.memory.manager import MemoryManager
from src.tools.registry import create_default_tools
from src.ui.config_manager import apply_user_overrides, load_user_config, save_user_config
from src.ui.user_config import ApiKeyConfig, UIConfig, UserConfig, UserLLMConfig, UserMemoryConfig, UserRagConfig


class UIBackend(QObject):
    """UI 与 Agent 核心的桥接"""

    # ---- Signals → QML ----
    responseReady = Signal(str)
    mainReady = Signal(str)
    subReady = Signal(str)
    modeChanged = Signal(str)
    characterStateChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._agent = None
        self._planner = None
        self._executor = None
        self._plan_manager = None
        self._tools = []
        self._memory = None
        self._initialized = False
        self._user_config = None
        self._desktop_app = None

        self._init_backend()

    def _init_backend(self):
        try:
            load_config()
            self._user_config = load_user_config()
            apply_user_overrides(self._user_config)

            self._llm = get_llm()
            self._tools = create_default_tools()
            self._memory = MemoryManager(self._llm)

            # 初始化 RAG 工具
            try:
                from src.rag.manager import KnowledgeBaseManager
                kb_mgr = KnowledgeBaseManager()
                for tool in self._tools:
                    if hasattr(tool, "set_manager") and "rag" in getattr(tool, "category", ""):
                        tool.set_manager(kb_mgr)
                    if hasattr(tool, "set_memory_manager"):
                        tool.set_memory_manager(self._memory)
            except Exception as e:
                logger.warning(f"RAG 初始化失败: {e}")

            # 初始化 Plan Manager
            try:
                from src.planning.manager import PlanManager
                self._plan_manager = PlanManager()
                self._plan_manager.init_db()
            except Exception as e:
                logger.warning(f"Plan Manager 初始化失败: {e}")

            self._initialized = True
            logger.info("UI Backend 已初始化")
        except Exception as e:
            logger.error(f"UI Backend 初始化失败: {e}")

    # ---- 懒加载 Agent ----
    def _ensure_agent(self):
        if self._agent is None and self._initialized:
            from src.core.agent import Agent
            self._agent = Agent(self._llm, self._tools, memory_manager=self._memory, mode="execute")

    # ---- Slots ← QML ----

    @Slot(str)
    def submitInput(self, text: str):
        """用户提交输入"""
        logger.info(f"UI 输入: {text[:80]}...")
        self.characterStateChanged.emit("thinking")
        self._ensure_agent()

        try:
            result = self._agent.run(text)
            output = result.get("output", "无输出")
            main_text = result.get("main", output)
            sub_text = result.get("sub", "")
            self.responseReady.emit(output)
            self.mainReady.emit(main_text)
            self.subReady.emit(sub_text)
            self.characterStateChanged.emit("happy")
        except Exception as e:
            self.responseReady.emit(f"❌ 错误: {e}")
            self.characterStateChanged.emit("busy")

        # 恢复 idle
        from PySide6.QtCore import QTimer
        QTimer.singleShot(4000, lambda: self.characterStateChanged.emit("idle"))

    @Slot()
    def toggleMode(self):
        """切换 Plan/Execute 模式"""
        self._ensure_agent()
        if self._agent is None:
            return
        current = self._agent.mode
        new = "plan" if current == "execute" else "execute"
        self._agent.set_mode(new)
        self.modeChanged.emit(new)

    @Slot(str)
    def switchLayout(self, layout: str):
        """切换界面布局 sleep ↔ classic"""
        if self._desktop_app and hasattr(self._desktop_app, "switch_layout"):
            self._desktop_app.switch_layout(layout)

    @Slot(str)
    def executePlan(self, plan_id: str):
        """执行指定计划"""
        if self._executor is None:
            from src.planning.executor import ExecuteModeAgent
            self._executor = ExecuteModeAgent(self._llm, self._tools)

        try:
            result = self._executor.execute_plan(plan_id)
            self.responseReady.emit(result)
        except Exception as e:
            self.responseReady.emit(f"❌ 执行失败: {e}")

    @Slot(str)
    def createPlan(self, description: str):
        """创建新计划"""
        if self._planner is None:
            from src.planning.planner import PlanModeAgent
            self._planner = PlanModeAgent(self._llm, self._tools)

        try:
            result = self._planner.generate_plan(description)
            self.responseReady.emit(result)
        except Exception as e:
            self.responseReady.emit(f"❌ 计划创建失败: {e}")

    @Slot(result="QVariantList")
    def listPlans(self):
        """获取计划列表"""
        if self._plan_manager is None:
            return []
        plans = self._plan_manager.list_plans()
        return [
            {
                "id": p.id,
                "title": p.title,
                "status": p.status,
                "completed_steps": p.completed_steps,
                "total_steps": p.total_steps,
            }
            for p in plans
        ]

    # ---- Settings Slots ----

    @Slot(result="QVariantMap")
    def loadSettings(self):
        """加载用户设置 → QML"""
        uc = self._user_config or load_user_config()
        return {
            "llm_model": uc.llm.default_model or get_config().llm.default_model,
            "temperature": uc.llm.temperature or get_config().llm.temperature,
            "max_tokens": uc.llm.max_tokens or get_config().llm.max_tokens,
            "streaming": uc.llm.streaming if uc.llm.streaming is not None else get_config().llm.streaming,

            "openai_key": uc.api_keys.openai_api_key,
            "anthropic_key": uc.api_keys.anthropic_api_key,
            "dashscope_key": uc.api_keys.dashscope_api_key,
            "deepseek_key": uc.api_keys.deepseek_api_key,
            "ollama_url": uc.api_keys.ollama_base_url,

            "embed_provider": uc.rag.embedding_provider or get_config().rag.embedding_provider,
            "embed_model": uc.rag.embedding_model or get_config().rag.embedding_model,

            "chunk_size": uc.rag.chunk_size or get_config().rag.chunk_size,
            "chunk_overlap": uc.rag.chunk_overlap or get_config().rag.chunk_overlap,
            "chunk_strategy": uc.rag.chunk_strategy or get_config().rag.chunk_strategy,
            "rag_top_k": uc.rag.default_top_k or get_config().rag.default_top_k,
            "hybrid_alpha": uc.rag.hybrid_alpha or get_config().rag.hybrid_alpha,

            "buffer_tokens": uc.memory.buffer_max_tokens or get_config().memory.buffer_max_tokens,
            "semantic_top_k": uc.memory.semantic_top_k or get_config().memory.semantic_top_k,

            "theme": uc.ui.theme,
            "font_size": uc.ui.font_size,
            "auto_hide": uc.ui.auto_hide_seconds,
            "hotkey": uc.ui.hotkey,
            "char_visible": uc.ui.character_visible,
            "char_position": uc.ui.character_position,
            "ui_layout": uc.ui.layout,
        }

    @Slot("QVariantMap")
    def saveSettings(self, settings: dict):
        """保存用户设置"""
        uc = self._user_config or UserConfig()

        uc.llm = UserLLMConfig(
            default_model=str(settings.get("llm_model", "")),
            temperature=float(settings.get("temperature", 0.7)),
            max_tokens=int(settings.get("max_tokens", 4096)),
            streaming=bool(settings.get("streaming", True)),
        )
        uc.api_keys = ApiKeyConfig(
            openai_api_key=str(settings.get("openai_key", "")),
            anthropic_api_key=str(settings.get("anthropic_key", "")),
            dashscope_api_key=str(settings.get("dashscope_key", "")),
            deepseek_api_key=str(settings.get("deepseek_key", "")),
            ollama_base_url=str(settings.get("ollama_url", "http://localhost:11434")),
        )
        uc.rag = UserRagConfig(
            embedding_provider=str(settings.get("embed_provider", "")),
            embedding_model=str(settings.get("embed_model", "")),
            chunk_size=int(settings.get("chunk_size", 500)),
            chunk_overlap=int(settings.get("chunk_overlap", 50)),
            chunk_strategy=str(settings.get("chunk_strategy", "")),
            default_top_k=int(settings.get("rag_top_k", 5)),
            hybrid_alpha=float(settings.get("hybrid_alpha", 0.7)),
        )
        uc.memory = UserMemoryConfig(
            buffer_max_tokens=int(settings.get("buffer_tokens", 4000)),
            semantic_top_k=int(settings.get("semantic_top_k", 5)),
        )
        uc.ui = UIConfig(
            theme=str(settings.get("theme", "dark")),
            font_size=int(settings.get("font_size", 14)),
            auto_hide_seconds=int(settings.get("auto_hide", 0)),
            hotkey=str(settings.get("hotkey", "Alt+Space")),
            character_visible=bool(settings.get("char_visible", True)),
            character_position=str(settings.get("char_position", "right")),
            layout=str(settings.get("ui_layout", "sleep")),
        )

        save_user_config(uc)
        apply_user_overrides(uc)
        self._user_config = uc

        # 重新初始化 Agent（如果模型变更）
        self._agent = None
        logger.info("设置已保存并应用")

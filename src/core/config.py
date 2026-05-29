"""配置管理 — 加载 YAML 配置 + 环境变量"""

from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentConfig(BaseModel):
    name: str = "Agent开发助手"
    max_iterations: int = 10
    verbose: bool = True
    stop_on_error: bool = True


class LLMConfig(BaseModel):
    default_model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 4096
    streaming: bool = True


class MemoryConfig(BaseModel):
    buffer_max_tokens: int = 4000
    summary_trigger_tokens: int = 3000
    semantic_top_k: int = 5
    episodic_top_k: int = 3
    importance_threshold: float = 0.5


class CompressionConfig(BaseModel):
    max_context_tokens: int = 8000
    strategy_sequence: list[str] = Field(default_factory=lambda: ["window", "summarize", "retrieve"])
    summary_max_tokens: int = 500


class ClassifierConfig(BaseModel):
    watch_directories: list[str] = Field(default_factory=list)
    default_rules_enabled: bool = True
    auto_categorize: bool = False


class SchedulerConfig(BaseModel):
    enabled: bool = False
    max_reminders: int = 50


class RagConfig(BaseModel):
    database_url: str = "sqlite:///data/knowledge.db"
    chroma_persist_dir: str = "data/chroma_kb"
    embedding_provider: str = "openai"
    embedding_model: str = "text-embedding-3-small"
    embedding_base_url: str = ""
    chunk_size: int = 500
    chunk_overlap: int = 50
    chunk_strategy: str = "recursive"
    default_top_k: int = 5
    hybrid_alpha: float = 0.7
    vector_top_k: int = 10
    bm25_top_k: int = 10


class StorageConfig(BaseModel):
    database_url: str = "sqlite:///data/agent.db"
    chroma_persist_dir: str = "data/chroma"


class PlanningConfig(BaseModel):
    plans_dir: str = "data/plans"
    template_path: str = "config/plan-template.md"
    auto_save: bool = True
    max_steps_per_plan: int = 20


class FormatConfig(BaseModel):
    main_tag: str = "【回】"
    sub_tag: str = "【细】"
    main_font_size: int = 15
    sub_font_size: int = 12
    sub_color: str = "#808090"
    style: str = "childlike"
    tone_words: list[str] = Field(default_factory=lambda: ["嘞", "嘿", "嘻", "吁"])


class LoggingConfig(BaseModel):
    level: str = "INFO"
    file: str = "data/logs/agent.log"
    rotation: str = "10 MB"
    retention: str = "7 days"


class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AGENT_", env_nested_delimiter="__")

    agent: AgentConfig = Field(default_factory=AgentConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    compression: CompressionConfig = Field(default_factory=CompressionConfig)
    rag: RagConfig = Field(default_factory=RagConfig)
    planning: PlanningConfig = Field(default_factory=PlanningConfig)
    format: FormatConfig = Field(default_factory=FormatConfig)
    classifier: ClassifierConfig = Field(default_factory=ClassifierConfig)
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


class ModelInfo(BaseModel):
    name: str
    provider: str
    model_id: str
    api_key_env: Optional[str] = None
    base_url: Optional[str] = None
    description: str = ""


class ModelsConfig(BaseModel):
    models: list[ModelInfo]


_config: Optional[AppConfig] = None
_models_config: Optional[ModelsConfig] = None


def _get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def load_config(config_path: Optional[str] = None) -> AppConfig:
    global _config
    if _config is not None:
        return _config

    if config_path is None:
        config_path = str(_get_project_root() / "config" / "default.yaml")

    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    _config = AppConfig(**data)
    return _config


def load_models(models_path: Optional[str] = None) -> ModelsConfig:
    global _models_config
    if _models_config is not None:
        return _models_config

    if models_path is None:
        models_path = str(_get_project_root() / "config" / "models.yaml")

    with open(models_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    _models_config = ModelsConfig(**data)
    return _models_config


def get_config() -> AppConfig:
    if _config is None:
        return load_config()
    return _config


def get_models() -> ModelsConfig:
    if _models_config is None:
        return load_models()
    return _models_config


def reset_config() -> None:
    global _config, _models_config
    _config = None
    _models_config = None

"""用户配置模型 — user.yaml"""

from typing import Optional

from pydantic import BaseModel, Field


class UIConfig(BaseModel):
    theme: str = "dark"
    font_size: int = 14
    auto_hide_seconds: int = 0
    hotkey: str = "Alt+Space"
    character_visible: bool = True
    character_position: str = "left"
    auto_start: bool = False


class ApiKeyConfig(BaseModel):
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    dashscope_api_key: str = ""
    deepseek_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"


class UserLLMConfig(BaseModel):
    default_model: str = ""
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    streaming: Optional[bool] = None


class UserMemoryConfig(BaseModel):
    buffer_max_tokens: Optional[int] = None
    semantic_top_k: Optional[int] = None
    episodic_top_k: Optional[int] = None
    importance_threshold: Optional[float] = None


class UserRagConfig(BaseModel):
    embedding_provider: str = ""
    embedding_model: str = ""
    embedding_base_url: str = ""
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None
    chunk_strategy: str = ""
    default_top_k: Optional[int] = None
    hybrid_alpha: Optional[float] = None


class UserConfig(BaseModel):
    ui: UIConfig = Field(default_factory=UIConfig)
    api_keys: ApiKeyConfig = Field(default_factory=ApiKeyConfig)
    llm: UserLLMConfig = Field(default_factory=UserLLMConfig)
    memory: UserMemoryConfig = Field(default_factory=UserMemoryConfig)
    rag: UserRagConfig = Field(default_factory=UserRagConfig)

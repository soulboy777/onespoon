"""用户配置管理器 — 读写 user.yaml"""

import os
from pathlib import Path
from typing import Optional

import yaml
from loguru import logger

from src.ui.user_config import UserConfig


def _get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def _get_user_config_path() -> str:
    return str(_get_project_root() / "config" / "user.yaml")


def load_user_config() -> UserConfig:
    """加载用户配置"""
    path = _get_user_config_path()

    if not os.path.exists(path):
        return _create_default_user_config()

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return UserConfig(**data)
    except Exception as e:
        logger.warning(f"user.yaml 解析失败，使用默认: {e}")
        return _create_default_user_config()


def save_user_config(config: UserConfig) -> None:
    """保存用户配置"""
    path = _get_user_config_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)

    data = config.model_dump(exclude_defaults=False)

    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, indent=2)

    _apply_env_vars(config)
    logger.info(f"用户配置已保存: {path}")


def _create_default_user_config() -> UserConfig:
    config = UserConfig()
    save_user_config(config)
    return config


def _apply_env_vars(config: UserConfig) -> None:
    """将 API Keys 设为环境变量"""
    keys = config.api_keys
    if keys.openai_api_key:
        os.environ["OPENAI_API_KEY"] = keys.openai_api_key
    if keys.anthropic_api_key:
        os.environ["ANTHROPIC_API_KEY"] = keys.anthropic_api_key
    if keys.dashscope_api_key:
        os.environ["DASHSCOPE_API_KEY"] = keys.dashscope_api_key
    if keys.deepseek_api_key:
        os.environ["DEEPSEEK_API_KEY"] = keys.deepseek_api_key
    if keys.ollama_base_url:
        os.environ["OLLAMA_HOST"] = keys.ollama_base_url


def apply_user_overrides(user_config: UserConfig) -> None:
    """将用户配置覆盖写入 default config（用于 Agent 启动前）"""
    from src.core.config import get_config

    app_config = get_config()

    ucfg = user_config

    # LLM 覆盖
    if ucfg.llm.default_model:
        app_config.llm.default_model = ucfg.llm.default_model
    if ucfg.llm.temperature is not None:
        app_config.llm.temperature = ucfg.llm.temperature
    if ucfg.llm.max_tokens is not None:
        app_config.llm.max_tokens = ucfg.llm.max_tokens
    if ucfg.llm.streaming is not None:
        app_config.llm.streaming = ucfg.llm.streaming

    # Memory 覆盖
    if ucfg.memory.buffer_max_tokens is not None:
        app_config.memory.buffer_max_tokens = ucfg.memory.buffer_max_tokens
    if ucfg.memory.semantic_top_k is not None:
        app_config.memory.semantic_top_k = ucfg.memory.semantic_top_k
    if ucfg.memory.episodic_top_k is not None:
        app_config.memory.episodic_top_k = ucfg.memory.episodic_top_k
    if ucfg.memory.importance_threshold is not None:
        app_config.memory.importance_threshold = ucfg.memory.importance_threshold

    # RAG 覆盖
    if ucfg.rag.embedding_provider:
        app_config.rag.embedding_provider = ucfg.rag.embedding_provider
    if ucfg.rag.embedding_model:
        app_config.rag.embedding_model = ucfg.rag.embedding_model
    if ucfg.rag.embedding_base_url:
        app_config.rag.embedding_base_url = ucfg.rag.embedding_base_url
    if ucfg.rag.chunk_size is not None:
        app_config.rag.chunk_size = ucfg.rag.chunk_size
    if ucfg.rag.chunk_overlap is not None:
        app_config.rag.chunk_overlap = ucfg.rag.chunk_overlap
    if ucfg.rag.chunk_strategy:
        app_config.rag.chunk_strategy = ucfg.rag.chunk_strategy
    if ucfg.rag.default_top_k is not None:
        app_config.rag.default_top_k = ucfg.rag.default_top_k
    if ucfg.rag.hybrid_alpha is not None:
        app_config.rag.hybrid_alpha = ucfg.rag.hybrid_alpha

    _apply_env_vars(ucfg)

"""LLM 抽象层 — 多模型适配（OpenAI / Claude / Ollama / 兼容接口）"""

from typing import Optional

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from loguru import logger

from src.core.config import ModelInfo, get_config, get_models


class LLMFactory:
    """模型工厂：根据配置创建 LangChain ChatModel 实例"""

    def __init__(self) -> None:
        self._models_config = get_models()
        self._app_config = get_config()
        self._model_map: dict[str, ModelInfo] = {
            m.name: m for m in self._models_config.models
        }

    def list_models(self) -> list[ModelInfo]:
        return self._models_config.models

    def get_model_info(self, name: str) -> Optional[ModelInfo]:
        return self._model_map.get(name)

    def create(self, model_name: Optional[str] = None, **kwargs) -> BaseChatModel:
        """创建 LLM 实例"""
        name = model_name or self._app_config.llm.default_model
        info = self._model_map.get(name)

        if info is None:
            logger.warning(f"模型 '{name}' 未配置，降级使用默认模型")
            info = self._model_map.get(self._app_config.llm.default_model)
            if info is None:
                raise ValueError(f"无可用模型。检查 config/models.yaml")

        return self._build_from_info(info, **kwargs)

    def _build_from_info(self, info: ModelInfo, **kwargs) -> BaseChatModel:
        provider = info.provider.lower()
        temperature = kwargs.pop("temperature", self._app_config.llm.temperature)
        max_tokens = kwargs.pop("max_tokens", self._app_config.llm.max_tokens)
        streaming = kwargs.pop("streaming", self._app_config.llm.streaming)

        if provider == "openai":
            return ChatOpenAI(
                model=info.model_id,
                temperature=temperature,
                max_tokens=max_tokens,
                streaming=streaming,
                **kwargs,
            )

        elif provider == "openai_compatible":
            base_url = info.base_url or kwargs.pop("base_url", None)
            return ChatOpenAI(
                model=info.model_id,
                temperature=temperature,
                max_tokens=max_tokens,
                streaming=streaming,
                base_url=base_url,
                **kwargs,
            )

        elif provider == "anthropic":
            from langchain_anthropic import ChatAnthropic

            return ChatAnthropic(
                model=info.model_id,
                temperature=temperature,
                max_tokens=max_tokens,
                streaming=streaming,
                **kwargs,
            )

        elif provider == "ollama":
            from langchain_community.chat_models import ChatOllama

            return ChatOllama(
                model=info.model_id,
                temperature=temperature,
                base_url=info.base_url or "http://localhost:11434",
                **kwargs,
            )

        else:
            raise ValueError(f"不支持的 provider: {provider}")


_llm_factory: Optional[LLMFactory] = None


def get_llm_factory() -> LLMFactory:
    global _llm_factory
    if _llm_factory is None:
        _llm_factory = LLMFactory()
    return _llm_factory


def get_llm(model_name: Optional[str] = None, **kwargs) -> BaseChatModel:
    return get_llm_factory().create(model_name, **kwargs)

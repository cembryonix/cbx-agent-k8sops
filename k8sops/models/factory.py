"""LLM model factory for creating chat models."""

import logging
from typing import Literal

from langchain_core.language_models.chat_models import BaseChatModel

from k8sops.config import get_llm_settings

logger = logging.getLogger(__name__)


def create_model(
    provider: Literal["anthropic", "openai", "ollama"] | None = None,
    model_name: str | None = None,
    temperature: float = 0.0,
    **kwargs,
) -> BaseChatModel:
    """Create a chat model based on provider.

    Args:
        provider: LLM provider (anthropic, openai, ollama). Defaults to settings.
        model_name: Model name. Defaults to settings.
        temperature: Model temperature. Defaults to 0.0.
        **kwargs: Additional model-specific arguments.

    Returns:
        LangChain chat model instance

    Raises:
        ValueError: If provider is not supported or API key is missing
    """
    settings = get_llm_settings()
    provider = provider or settings.provider
    model_name = model_name or settings.model_name

    logger.info(f"Creating {provider} model: {model_name}")

    if provider == "anthropic":
        return _create_anthropic_model(model_name, temperature, **kwargs)
    elif provider == "openai":
        return _create_openai_model(model_name, temperature, **kwargs)
    elif provider == "ollama":
        return _create_ollama_model(model_name, temperature, **kwargs)
    else:
        raise ValueError(f"Unsupported provider: {provider}")


def _create_anthropic_model(
    model_name: str,
    temperature: float,
    **kwargs,
) -> BaseChatModel:
    """Create Anthropic Claude model."""
    from langchain_anthropic import ChatAnthropic

    settings = get_llm_settings()
    if not settings.anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY is required for Anthropic provider")

    return ChatAnthropic(
        model=model_name,
        temperature=temperature,
        api_key=settings.anthropic_api_key,
        **kwargs,
    )


def _create_openai_model(
    model_name: str,
    temperature: float,
    **kwargs,
) -> BaseChatModel:
    """Create OpenAI model."""
    from langchain_openai import ChatOpenAI

    settings = get_llm_settings()
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is required for OpenAI provider")

    return ChatOpenAI(
        model=model_name,
        temperature=temperature,
        api_key=settings.openai_api_key,
        **kwargs,
    )


def _create_ollama_model(
    model_name: str,
    temperature: float,
    **kwargs,
) -> BaseChatModel:
    """Create Ollama local model."""
    from langchain_ollama import ChatOllama

    settings = get_llm_settings()

    return ChatOllama(
        model=model_name,
        temperature=temperature,
        base_url=settings.ollama_base_url,
        **kwargs,
    )

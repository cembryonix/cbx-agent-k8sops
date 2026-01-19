"""Embedding model factory.

Note: Anthropic does not provide an embeddings API.
Use OpenAI or Ollama for embeddings even when using Anthropic for chat.
"""

import logging
from typing import Literal

from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings
from langchain_ollama import OllamaEmbeddings

from k8sops.config import get_llm_settings

logger = logging.getLogger(__name__)


def create_embeddings(
    provider: Literal["openai", "ollama"],
    model: str | None = None,
) -> Embeddings:
    """Create an embeddings model.

    Args:
        provider: Embedding provider ("openai" or "ollama").
        model: Model name. Defaults per provider if not specified.

    Returns:
        Embeddings instance.

    Raises:
        ValueError: If provider is unknown.
    """
    llm_settings = get_llm_settings()

    if provider == "openai":
        model_name = model or "text-embedding-3-small"
        logger.info(f"Creating OpenAI embeddings: {model_name}")
        return OpenAIEmbeddings(
            model=model_name,
            api_key=llm_settings.openai_api_key,
        )

    elif provider == "ollama":
        model_name = model or "nomic-embed-text"
        base_url = llm_settings.ollama_base_url or "http://localhost:11434"
        logger.info(f"Creating Ollama embeddings: {model_name} at {base_url}")
        return OllamaEmbeddings(model=model_name, base_url=base_url)

    else:
        raise ValueError(
            f"Unknown embedding provider: {provider}. Use 'openai' or 'ollama'."
        )
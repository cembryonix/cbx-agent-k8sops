"""Application settings using pydantic-settings."""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Literal


class LLMSettings(BaseSettings):
    """LLM provider configuration."""

    provider: Literal["anthropic", "openai", "ollama"] = Field(
        default="anthropic",
        alias="LLM_PROVIDER",
    )
    model_name: str = Field(
        default="claude-sonnet-4-20250514",
        alias="MODEL_NAME",
    )
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        alias="OLLAMA_BASE_URL",
    )

    model_config = {"env_file": ".env", "extra": "ignore"}


class MCPSettings(BaseSettings):
    """MCP server configuration."""

    transport: Literal["stdio", "http"] = Field(default="http", alias="MCP_TRANSPORT")

    # HTTP transport
    server_url: str | None = Field(default=None, alias="MCP_SERVER_URL")
    ssl_verify: bool = Field(default=True, alias="MCP_SSL_VERIFY")

    # stdio transport
    command: str = Field(default="python", alias="MCP_SERVER_COMMAND")
    args: str = Field(default="", alias="MCP_SERVER_ARGS")

    model_config = {"env_file": ".env", "extra": "ignore"}

    def get_stdio_args(self) -> list[str]:
        """Parse args string into list."""
        return self.args.split() if self.args else []


class AppSettings(BaseSettings):
    """Application settings."""

    debug: bool = Field(default=False, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Maximum number of sessions per user
    max_sessions: int = Field(default=10, alias="MAX_SESSIONS")

    model_config = {"env_file": ".env", "extra": "ignore"}


class MemorySettings(BaseSettings):
    """Agent memory configuration."""

    # Redis URL for short-term memory (checkpointer) and long-term memory (store)
    # If not set, uses in-memory storage (not persistent)
    redis_url: str | None = Field(default=None, alias="REDIS_URL")

    # Use shallow checkpointer (only stores latest state, not full history)
    # Recommended for production to reduce memory usage
    shallow: bool = Field(default=False, alias="MEMORY_SHALLOW")

    # Long-term memory settings
    long_term_enabled: bool = Field(default=False, alias="MEMORY_LONG_TERM_ENABLED")

    # Embedding provider for semantic search (openai or ollama)
    # Note: Anthropic doesn't provide embeddings, use OpenAI or Ollama
    embedding_provider: Literal["openai", "ollama"] = Field(
        default="openai",
        alias="EMBEDDING_PROVIDER",
    )

    # Embedding model name (defaults per provider if not specified)
    # OpenAI: text-embedding-3-small (1536 dims)
    # Ollama: nomic-embed-text (768 dims)
    embedding_model: str | None = Field(default=None, alias="EMBEDDING_MODEL")

    # Embedding dimensions (auto-detected for known models if not specified)
    embedding_dims: int | None = Field(default=None, alias="EMBEDDING_DIMS")

    # Context window management - threshold (0.0-1.0) that triggers summarization
    context_threshold: float = Field(default=0.75, alias="MEMORY_CONTEXT_THRESHOLD")

    # Maximum token count for context (model-specific, sensible default)
    max_context_tokens: int = Field(default=100000, alias="MEMORY_MAX_CONTEXT_TOKENS")

    # Number of long-term memories to retrieve per search
    max_memories: int = Field(default=5, alias="MEMORY_MAX_MEMORIES")

    # User ID for memory namespace (use "default" when no auth)
    user_id: str = Field(default="default", alias="MEMORY_USER_ID")

    model_config = {"env_file": ".env", "extra": "ignore"}

    @property
    def use_redis(self) -> bool:
        """Check if Redis is configured."""
        return self.redis_url is not None

    @property
    def use_long_term(self) -> bool:
        """Check if long-term memory is enabled and configured."""
        return self.long_term_enabled and self.use_redis

    def get_embedding_model(self) -> str:
        """Get embedding model with provider-specific defaults."""
        if self.embedding_model:
            return self.embedding_model
        if self.embedding_provider == "openai":
            return "text-embedding-3-small"
        return "nomic-embed-text"

    def get_embedding_dims(self) -> int:
        """Get embedding dimensions, with defaults for known models."""
        if self.embedding_dims:
            return self.embedding_dims

        model = self.get_embedding_model()
        known_dims = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
            "nomic-embed-text": 768,
            "mxbai-embed-large": 1024,
            "all-minilm": 384,
        }

        return known_dims.get(model, 1536 if self.embedding_provider == "openai" else 768)


# Singleton instances
_llm_settings: LLMSettings | None = None
_mcp_settings: MCPSettings | None = None
_app_settings: AppSettings | None = None
_memory_settings: MemorySettings | None = None


def get_llm_settings() -> LLMSettings:
    """Get LLM settings singleton."""
    global _llm_settings
    if _llm_settings is None:
        _llm_settings = LLMSettings()
    return _llm_settings


def get_mcp_settings() -> MCPSettings:
    """Get MCP settings singleton."""
    global _mcp_settings
    if _mcp_settings is None:
        _mcp_settings = MCPSettings()
    return _mcp_settings


def get_app_settings() -> AppSettings:
    """Get app settings singleton."""
    global _app_settings
    if _app_settings is None:
        _app_settings = AppSettings()
    return _app_settings


def get_memory_settings() -> MemorySettings:
    """Get memory settings singleton."""
    global _memory_settings
    if _memory_settings is None:
        _memory_settings = MemorySettings()
    return _memory_settings

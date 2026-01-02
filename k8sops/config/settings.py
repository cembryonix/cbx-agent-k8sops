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

    model_config = {"env_file": ".env", "extra": "ignore"}


# Singleton instances
_llm_settings: LLMSettings | None = None
_mcp_settings: MCPSettings | None = None
_app_settings: AppSettings | None = None


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

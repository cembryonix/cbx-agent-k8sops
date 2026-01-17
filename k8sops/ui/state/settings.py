"""Settings state management for the K8S Ops Agent UI."""

import reflex as rx
from typing import Literal

from k8sops.config import (
    get_model_ids_for_provider,
    get_default_model,
    get_default_provider,
)

# Load defaults from config at module level (from config/defaults/models.yaml)
default_provider = get_default_provider()
default_model = get_default_model(default_provider)


class SettingsState(rx.State):
    """State for application settings.

    When model-affecting settings (provider, model_name, temperature) change,
    triggers ChatState.reinitialize_agent() to recreate the agent.

    Provider and model lists are loaded from config/defaults/models.yaml.
    """

    # LLM settings - defaults loaded from config/defaults/models.yaml
    llm_provider: str = default_provider
    model_name: str = default_model
    temperature: float = 0.0

    # MCP settings
    mcp_transport: Literal["stdio", "http"] = "http"
    mcp_server_url: str = ""

    # UI settings (don't affect agent)
    show_tool_calls: bool = True
    stream_responses: bool = True

    def set_provider(self, provider: str):
        """Set LLM provider and reinitialize agent."""
        if self.llm_provider == provider:
            return

        self.llm_provider = provider

        # Update model name to default for new provider (from config)
        self.model_name = get_default_model(provider)

        # Trigger agent reinitialization
        return ChatState.reinitialize_agent

    def set_model_name(self, name: str):
        """Set model name and reinitialize agent."""
        if self.model_name == name:
            return

        self.model_name = name

        # Trigger agent reinitialization
        return ChatState.reinitialize_agent

    def set_temperature(self, temp: float):
        """Set temperature and reinitialize agent."""
        if self.temperature == temp:
            return

        self.temperature = temp

        # Trigger agent reinitialization
        return ChatState.reinitialize_agent

    def set_mcp_url(self, url: str):
        """Set MCP server URL."""
        self.mcp_server_url = url

    def toggle_tool_calls(self):
        """Toggle tool call visibility (UI only, no agent reinit)."""
        self.show_tool_calls = not self.show_tool_calls

    def toggle_streaming(self):
        """Toggle response streaming (UI only, no agent reinit)."""
        self.stream_responses = not self.stream_responses

    @rx.var
    def available_models(self) -> list[str]:
        """Get available models for current provider (from config)."""
        return get_model_ids_for_provider(self.llm_provider)


# Import here to avoid circular import
from .chat import ChatState

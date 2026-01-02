"""Base state for the application."""

import reflex as rx


class BaseState(rx.State):
    """Base state with common functionality."""

    # Theme
    dark_mode: bool = True

    # Sidebar
    sidebar_open: bool = True

    # Settings
    selected_model: str = "claude-sonnet"
    mcp_server_url: str = "https://cbx-mcp-k8s.vvklab.cloud.cembryonix.com/mcp"

    def toggle_dark_mode(self):
        """Toggle dark/light mode."""
        self.dark_mode = not self.dark_mode

    def toggle_sidebar(self):
        """Toggle sidebar visibility."""
        self.sidebar_open = not self.sidebar_open

    def set_model(self, value: str):
        """Update selected model."""
        self.selected_model = value

    def set_mcp_server_url(self, value: str):
        """Update MCP server URL."""
        self.mcp_server_url = value

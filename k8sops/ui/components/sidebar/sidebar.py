"""Main sidebar component - Clean minimal design."""

import reflex as rx
from ...state import ChatState, BaseState
from ...state.settings import SettingsState


def settings_popover() -> rx.Component:
    """Settings popover with provider and model selection."""
    return rx.popover.root(
        rx.popover.trigger(
            rx.button(
                rx.icon("settings", size=16),
                rx.text("Settings"),
                variant="ghost",
                width="100%",
                justify="start",
            ),
        ),
        rx.popover.content(
            rx.vstack(
                # Provider selection
                rx.box(
                    rx.text("Provider", font_size="0.875rem", font_weight="500", margin_bottom="0.5rem"),
                    rx.select.root(
                        rx.select.trigger(placeholder="Select provider..."),
                        rx.select.content(
                            rx.select.item("Anthropic", value="anthropic"),
                            rx.select.item("OpenAI", value="openai"),
                            rx.select.item("Ollama", value="ollama"),
                        ),
                        value=SettingsState.llm_provider,
                        on_change=SettingsState.set_provider,
                    ),
                    width="100%",
                ),
                # Model selection - dynamic based on provider
                rx.box(
                    rx.text("Model", font_size="0.875rem", font_weight="500", margin_bottom="0.5rem"),
                    rx.select.root(
                        rx.select.trigger(placeholder="Select model..."),
                        rx.select.content(
                            rx.foreach(
                                SettingsState.available_models,
                                lambda model: rx.select.item(model, value=model),
                            ),
                        ),
                        value=SettingsState.model_name,
                        on_change=SettingsState.set_model_name,
                    ),
                    width="100%",
                ),
                # Temperature slider
                rx.box(
                    rx.hstack(
                        rx.text("Temperature", font_size="0.875rem", font_weight="500"),
                        rx.spacer(),
                        rx.text(SettingsState.temperature, font_size="0.875rem", color="gray"),
                    ),
                    rx.slider(
                        value=[SettingsState.temperature],
                        min=0,
                        max=1,
                        step=0.1,
                        on_change=lambda val: SettingsState.set_temperature(val[0]),
                    ),
                    width="100%",
                    margin_top="0.5rem",
                ),
                # Divider
                rx.divider(margin_y="0.5rem"),
                # Current model display
                rx.hstack(
                    rx.text("Active Model", font_size="0.875rem"),
                    rx.spacer(),
                    rx.text(
                        ChatState.current_model,
                        font_size="0.75rem",
                        color="gray",
                        max_width="150px",
                        overflow="hidden",
                        text_overflow="ellipsis",
                    ),
                    width="100%",
                ),
                # Connection status
                rx.hstack(
                    rx.text("MCP Connected", font_size="0.875rem"),
                    rx.spacer(),
                    rx.cond(
                        ChatState.mcp_connected,
                        rx.icon("circle-check", size=16, color="green"),
                        rx.icon("circle-x", size=16, color="red"),
                    ),
                    width="100%",
                ),
                rx.hstack(
                    rx.text("Agent Ready", font_size="0.875rem"),
                    rx.spacer(),
                    rx.cond(
                        ChatState.agent_ready,
                        rx.icon("circle-check", size=16, color="green"),
                        rx.icon("circle-x", size=16, color="red"),
                    ),
                    width="100%",
                ),
                spacing="3",
                width="280px",
                padding="4px",
            ),
            side="top",
            align="start",
        ),
    )


def sidebar() -> rx.Component:
    """Render fixed sidebar."""
    return rx.cond(
        BaseState.sidebar_open,
        rx.box(
            # Header
            rx.hstack(
                rx.hstack(
                    rx.icon("server", size=24, color=rx.color("blue", 9)),
                    rx.text("K8S Ops Agent", font_weight="bold", font_size="18px"),
                    spacing="2",
                ),
                rx.icon_button(
                    rx.icon("panel-left-close", size=18),
                    on_click=BaseState.toggle_sidebar,
                    variant="ghost",
                ),
                justify="between",
                width="100%",
                padding="16px",
                border_bottom="1px solid",
                border_color=rx.color("gray", 4),
            ),
            # Spacer
            rx.box(flex="1"),
            # Bottom buttons
            rx.vstack(
                settings_popover(),
                rx.button(
                    rx.icon("trash-2", size=16),
                    rx.text("Clear Chat"),
                    on_click=ChatState.clear_chat,
                    variant="ghost",
                    width="100%",
                    justify="start",
                ),
                padding="12px",
                spacing="1",
                border_top="1px solid",
                border_color=rx.color("gray", 4),
            ),
            # Sidebar container styles
            width="240px",
            height="100vh",
            position="fixed",
            left="0",
            top="0",
            background_color=rx.color("gray", 2),
            border_right="1px solid",
            border_color=rx.color("gray", 4),
            display="flex",
            flex_direction="column",
            z_index="100",
        ),
    )


def sidebar_toggle() -> rx.Component:
    """Toggle button when sidebar is closed."""
    return rx.cond(
        ~BaseState.sidebar_open,
        rx.icon_button(
            rx.icon("panel-left-open", size=18),
            on_click=BaseState.toggle_sidebar,
            variant="ghost",
            position="fixed",
            left="12px",
            top="12px",
            z_index="100",
        ),
    )

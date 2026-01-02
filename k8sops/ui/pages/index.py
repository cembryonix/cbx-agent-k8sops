"""Main chat page."""

import reflex as rx
from ..state import ChatState, BaseState
from ..components import (
    message_list,
    input_bar,
    tool_calls_panel,
    sidebar,
    sidebar_toggle,
)


def chat_area() -> rx.Component:
    """Main chat area with messages and input."""
    return rx.vstack(
        # Error message
        rx.cond(
            ChatState.error_message != "",
            rx.box(
                rx.hstack(
                    rx.icon("circle-alert", size=16),
                    rx.text(ChatState.error_message),
                    rx.icon_button(
                        rx.icon("x", size=14),
                        on_click=ChatState.clear_error,
                        variant="ghost",
                        size="1",
                    ),
                    spacing="2",
                ),
                background_color=rx.color("red", 3),
                color=rx.color("red", 11),
                padding="12px 16px",
                margin="16px",
                border_radius="8px",
            ),
        ),
        # Messages (scrollable, takes remaining space)
        message_list(),
        # Tool calls panel (collapsible)
        tool_calls_panel(),
        # Input bar (fixed at bottom)
        input_bar(),
        height="100vh",
        width="100%",
        spacing="0",
    )


def index() -> rx.Component:
    """Main page layout."""
    return rx.box(
        # Fixed sidebar
        sidebar(),
        # Toggle button
        sidebar_toggle(),
        # Main content (offset by sidebar width)
        rx.box(
            chat_area(),
            margin_left=rx.cond(BaseState.sidebar_open, "240px", "0"),
            transition="margin-left 0.2s ease",
            height="100vh",
        ),
        background_color=rx.color("gray", 1),
        color=rx.color("gray", 12),
        min_height="100vh",
        on_mount=ChatState.initialize,
    )

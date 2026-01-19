"""Main chat page."""

import reflex as rx

from ..state import ChatState, BaseState
from ..styles import WARM_BG_MAIN
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
    """Main page layout with unified sidebar."""
    return rx.box(
        # Fixed sidebar
        sidebar(),
        # Toggle button when sidebar is closed
        sidebar_toggle(),
        # Chat area (offset by sidebar when open)
        rx.box(
            chat_area(),
            margin_left=rx.cond(BaseState.sidebar_open, "260px", "0"),
            transition="margin-left 0.2s ease",
            height="100vh",
        ),
        background_color=WARM_BG_MAIN,
        color=rx.color("gray", 12),
        min_height="100vh",
        on_mount=ChatState.initialize,
    )
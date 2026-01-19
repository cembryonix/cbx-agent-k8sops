"""Message list component."""

import reflex as rx
from ...state import ChatState
from .message import message_bubble


def message_list() -> rx.Component:
    """Render scrollable message list, centered with reasonable width."""
    return rx.auto_scroll(
        rx.box(
            rx.foreach(ChatState.messages, message_bubble),
            # Streaming indicator
            rx.cond(
                ChatState.is_streaming,
                rx.box(
                    rx.hstack(
                        rx.spinner(size="1"),
                        rx.text("Thinking...", font_size="0.875rem", color=rx.color("gray", 10)),
                        spacing="2",
                    ),
                    padding="12px 16px",
                    align_self="flex-start",
                ),
            ),
            width="100%",
            max_width="900px",
            margin="0 auto",
            display="flex",
            flex_direction="column",
            gap="12px",
        ),
        flex="1",
        padding="16px 48px",
        width="100%",
    )

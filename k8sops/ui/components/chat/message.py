"""Chat message component."""

import reflex as rx


def message_bubble(message: dict) -> rx.Component:
    """Render a chat message bubble.

    Args:
        message: Message dict with role and content

    Returns:
        Styled message bubble component
    """
    return rx.box(
        rx.cond(
            message["role"] == "user",
            # User messages are plain text
            rx.text(message["content"], white_space="pre-wrap"),
            # Assistant messages can have markdown
            rx.markdown(message["content"]),
        ),
        padding="12px 16px",
        border_radius="16px",
        max_width="85%",
        background_color=rx.cond(
            message["role"] == "user",
            rx.color("blue", 9),
            rx.color("gray", 4),
        ),
        color=rx.cond(
            message["role"] == "user",
            "white",
            rx.color("gray", 12),
        ),
        align_self=rx.cond(
            message["role"] == "user",
            "flex-end",
            "flex-start",
        ),
    )

"""Chat message component."""

import reflex as rx

# Warm background for assistant messages
WARM_ASSISTANT_BG = "#F0EDE5"

# Softer blue for user messages (less bright than blue-9)
USER_MESSAGE_BG = "#5B8DEF"

# Component map for better markdown rendering (especially tables)
markdown_component_map = {
    "table": lambda *children: rx.box(
        rx.el.table(
            *children,
            width="100%",
            border_collapse="collapse",
            font_size="0.875rem",
        ),
        overflow_x="auto",
        margin_y="0.5rem",
    ),
    "th": lambda *children: rx.el.th(
        *children,
        padding="8px 12px",
        text_align="left",
        font_weight="600",
        border_bottom="2px solid",
        border_color="#D4D0C8",
        background_color="#F5F2EA",
    ),
    "td": lambda *children: rx.el.td(
        *children,
        padding="8px 12px",
        border_bottom="1px solid",
        border_color="#E8E4DC",
    ),
    "tr": lambda *children: rx.el.tr(*children),
    "thead": lambda *children: rx.el.thead(*children),
    "tbody": lambda *children: rx.el.tbody(*children),
}


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
            # Assistant messages with markdown and better table rendering
            rx.markdown(message["content"], component_map=markdown_component_map),
        ),
        padding="12px 16px",
        border_radius="16px",
        # User messages more compact, agent messages full width
        max_width=rx.cond(
            message["role"] == "user",
            "75%",
            "100%",
        ),
        background_color=rx.cond(
            message["role"] == "user",
            USER_MESSAGE_BG,
            WARM_ASSISTANT_BG,
        ),
        color=rx.cond(
            message["role"] == "user",
            "white",
            rx.color("gray", 12),
        ),
        # Agent messages left-aligned, user messages right-aligned
        align_self=rx.cond(
            message["role"] == "user",
            "flex-end",
            "flex-start",
        ),
    )

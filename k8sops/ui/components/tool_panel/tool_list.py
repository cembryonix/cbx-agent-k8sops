"""Tool calls list component."""

import reflex as rx
from ...state import ChatState
from .tool_call import tool_call_item

from k8sops.ui.styles import (
    WARM_ASSISTANT_BG_LIGHT,
    DARK_ASSISTANT_BG,
)


def tool_calls_panel() -> rx.Component:
    """Render the collapsible panel showing all tool calls.

    Returns:
        Collapsible tool calls panel component
    """
    return rx.cond(
        ChatState.tool_calls.length() > 0,
        rx.box(
            rx.accordion.root(
                rx.accordion.item(
                    header=rx.hstack(
                        rx.icon(
                            "wrench",
                            size=14,
                            color=rx.color_mode_cond("gray.600", "gray.400"),
                        ),
                        rx.text(
                            "Tool Calls",
                            class_name="font-medium text-sm",
                            color=rx.color_mode_cond("gray.700", "gray.300"),
                        ),
                        rx.badge(
                            ChatState.tool_calls.length(),
                            color_scheme="blue",
                            size="1",
                        ),
                        class_name="gap-2",
                    ),
                    content=rx.box(
                        rx.foreach(
                            ChatState.tool_calls,
                            tool_call_item,
                        ),
                        max_height="24rem",
                        overflow_y="auto",
                        overflow_x="hidden",
                        padding="0.5rem",
                        width="100%",
                    ),
                    value="tool-calls",
                ),
                type="single",
                collapsible=True,
                variant="ghost",
                width="100%",
            ),
            background=rx.color_mode_cond(WARM_ASSISTANT_BG_LIGHT, DARK_ASSISTANT_BG),
            border_top=rx.color_mode_cond("1px solid #e5e5e5", "1px solid #333"),
            flex_shrink="0",
            width="100%",
            overflow="hidden",
        ),
    )

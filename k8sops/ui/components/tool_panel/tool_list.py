"""Tool calls list component."""

import reflex as rx
from ...state import ChatState
from .tool_call import tool_call_item


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
                        rx.icon("wrench", size=16),
                        rx.text("Tool Calls", class_name="font-medium"),
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
                        class_name="max-h-64 overflow-y-auto",
                    ),
                    value="tool-calls",
                ),
                type="single",
                collapsible=True,
                variant="ghost",
                class_name="w-full",
            ),
            class_name="border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 flex-shrink-0",
        ),
    )

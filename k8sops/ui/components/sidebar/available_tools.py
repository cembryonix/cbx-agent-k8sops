"""Available tools display in sidebar."""

import reflex as rx
from ...state import ChatState


def tool_item(tool: dict) -> rx.Component:
    """Render a single tool in the list.

    Args:
        tool: Tool definition dict with name and description

    Returns:
        Tool item component (compact, name only)
    """
    return rx.box(
        rx.hstack(
            rx.icon("terminal", size=14, class_name="text-gray-500"),
            rx.text(tool["name"], class_name="text-sm font-medium truncate"),
            class_name="gap-2",
        ),
        class_name="py-1.5 px-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded cursor-default",
    )


def available_tools_list() -> rx.Component:
    """Render the list of available MCP tools.

    Returns:
        Available tools list component
    """
    return rx.box(
        rx.hstack(
            rx.icon("wrench", size=16),
            rx.text("Available Tools", class_name="font-medium text-sm"),
            rx.badge(
                ChatState.available_tools.length(),
                color_scheme="blue",
                size="1",
            ),
            class_name="gap-2 mb-2",
        ),
        rx.cond(
            ChatState.available_tools.length() > 0,
            rx.box(
                rx.foreach(
                    ChatState.available_tools,
                    tool_item,
                ),
            ),
            rx.text(
                "No tools available",
                class_name="text-sm text-gray-500 italic",
            ),
        ),
        class_name="p-3",
    )

"""Tool call display component."""

import reflex as rx


def tool_call_item(tool_call: dict) -> rx.Component:
    """Render a single tool call.

    Args:
        tool_call: ToolCall dict

    Returns:
        Tool call display component
    """
    status_color = rx.match(
        tool_call["status"],
        ("running", "yellow"),
        ("complete", "green"),
        ("error", "red"),
        "gray",
    )

    return rx.box(
        # Header
        rx.hstack(
            rx.hstack(
                rx.icon("terminal", size=16),
                rx.text(tool_call["name"], class_name="font-medium"),
                class_name="gap-2",
            ),
            rx.badge(
                tool_call["status"],
                color_scheme=status_color,
                size="1",
            ),
            class_name="justify-between w-full",
        ),
        # Arguments (formatted JSON)
        rx.cond(
            tool_call["arguments"] != "",
            rx.box(
                rx.text("Arguments:", class_name="text-xs text-gray-500 mt-2"),
                rx.code_block(
                    tool_call["arguments"],
                    language="json",
                    show_line_numbers=False,
                    wrap_long_lines=True,
                    class_name="text-xs mt-1 max-h-32 overflow-y-auto",
                ),
            ),
        ),
        # Output (when complete, formatted)
        rx.cond(
            tool_call["status"] == "complete",
            rx.box(
                rx.text("Output:", class_name="text-xs text-gray-500 mt-2"),
                rx.code_block(
                    tool_call["output"],
                    language="json",
                    show_line_numbers=False,
                    wrap_long_lines=True,
                    class_name="text-xs mt-1 max-h-48 overflow-y-auto",
                ),
            ),
        ),
        # Error (if any)
        rx.cond(
            tool_call["error"] != "",
            rx.box(
                rx.text("Error:", class_name="text-xs text-red-500 mt-2"),
                rx.code(
                    tool_call["error"],
                    class_name="text-xs block mt-1 p-2 bg-red-50 dark:bg-red-900/20 rounded text-red-600",
                ),
            ),
        ),
        class_name="p-3 border border-gray-200 dark:border-gray-700 rounded-lg mb-2",
    )

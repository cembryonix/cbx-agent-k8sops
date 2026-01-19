"""Tool call display component."""

import reflex as rx

from k8sops.ui.styles import (
    WARM_BG_SIDEBAR_LIGHT,
    DARK_BG_SIDEBAR,
)


def _code_content_box(label: str, content: str, max_height: str = "8rem") -> rx.Component:
    """Render a code content box with proper text wrapping.

    Args:
        label: Label text (e.g., "Arguments:", "Output:")
        content: The content to display
        max_height: Maximum height with overflow scroll

    Returns:
        A styled code box component
    """
    return rx.box(
        rx.text(
            label,
            color=rx.color_mode_cond("gray.600", "gray.400"),
            class_name="text-xs font-medium mb-1",
        ),
        rx.box(
            rx.text(
                content,
                class_name="text-xs font-mono",
                style={
                    "white_space": "pre-wrap",
                    "word_break": "break-word",
                    "overflow_wrap": "break-word",
                },
            ),
            background=rx.color_mode_cond(WARM_BG_SIDEBAR_LIGHT, DARK_BG_SIDEBAR),
            border_radius="6px",
            padding="0.75rem",
            max_height=max_height,
            overflow_y="auto",
            overflow_x="hidden",
            width="100%",
        ),
        margin_bottom="0.5rem",
    )


def _tool_call_details(tool_call: dict) -> rx.Component:
    """Render the expandable details content for a tool call."""
    return rx.box(
        # Arguments (formatted)
        rx.cond(
            tool_call["arguments"] != "",
            _code_content_box("Arguments:", tool_call["arguments"], "10rem"),
        ),
        # Output (when complete)
        rx.cond(
            tool_call["status"] == "complete",
            _code_content_box("Output:", tool_call["output"], "14rem"),
        ),
        # Error (if any)
        rx.cond(
            tool_call["error"] != "",
            rx.box(
                rx.text(
                    "Error:",
                    class_name="text-xs font-medium mb-1",
                    color="red.500",
                ),
                rx.box(
                    rx.text(
                        tool_call["error"],
                        class_name="text-xs",
                        style={
                            "white_space": "pre-wrap",
                            "word_break": "break-word",
                        },
                    ),
                    background=rx.color_mode_cond("red.50", "rgba(127, 29, 29, 0.2)"),
                    color=rx.color_mode_cond("red.600", "red.400"),
                    border_radius="6px",
                    padding="0.75rem",
                ),
                margin_bottom="0.5rem",
            ),
        ),
        padding_top="0.5rem",
        width="100%",
        overflow="hidden",
    )


def tool_call_item(tool_call: dict) -> rx.Component:
    """Render a single collapsible tool call.

    Args:
        tool_call: ToolCall dict

    Returns:
        Collapsible tool call component
    """
    status_color = rx.match(
        tool_call["status"],
        ("running", "yellow"),
        ("complete", "green"),
        ("error", "red"),
        "gray",
    )

    return rx.accordion.root(
        rx.accordion.item(
            header=rx.hstack(
                rx.icon(
                    "terminal",
                    size=14,
                    color=rx.color_mode_cond("gray.600", "gray.400"),
                ),
                rx.text(
                    tool_call["name"],
                    class_name="font-medium text-sm",
                    color=rx.color_mode_cond("gray.800", "gray.200"),
                ),
                rx.badge(
                    tool_call["status"],
                    color_scheme=status_color,
                    size="1",
                ),
                class_name="gap-2",
            ),
            content=_tool_call_details(tool_call),
            value="details",
        ),
        type="single",
        collapsible=True,
        variant="ghost",
        background=rx.color_mode_cond("white", "#222"),
        border=rx.color_mode_cond("1px solid #e5e5e5", "1px solid #333"),
        border_radius="8px",
        margin_bottom="0.5rem",
        width="100%",
        overflow="hidden",
    )

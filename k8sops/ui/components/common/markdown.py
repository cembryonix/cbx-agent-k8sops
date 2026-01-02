"""Markdown rendering component."""

import reflex as rx


def markdown_content(content: str) -> rx.Component:
    """Render markdown content.

    Args:
        content: Markdown string to render

    Returns:
        Reflex component with rendered markdown
    """
    return rx.markdown(
        content,
        class_name="prose prose-sm dark:prose-invert max-w-none",
    )

"""Code block component with syntax highlighting."""

import reflex as rx


def code_block(code: str, language: str = "text") -> rx.Component:
    """Render a code block with syntax highlighting.

    Args:
        code: Code content
        language: Programming language for syntax highlighting

    Returns:
        Reflex component with syntax-highlighted code
    """
    return rx.box(
        rx.code_block(
            code,
            language=language,
            show_line_numbers=True,
            wrap_long_lines=True,
            class_name="text-sm",
        ),
        class_name="rounded-lg overflow-hidden my-2",
    )

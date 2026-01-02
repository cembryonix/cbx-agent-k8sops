"""Chat input bar component."""

import reflex as rx
from ...state import ChatState


def input_bar() -> rx.Component:
    """Render fixed input bar at bottom, centered."""
    return rx.box(
        rx.box(
            rx.hstack(
                rx.input(
                    value=ChatState.current_input,
                    on_change=ChatState.set_input,
                    on_key_down=ChatState.handle_key_down,
                    placeholder="Ask about your Kubernetes cluster...",
                    width="100%",
                    height="3rem",
                    padding_x="1rem",
                    font_size="1rem",
                    border_radius="1.5rem",
                    border="1px solid",
                    border_color=rx.color("gray", 6),
                    background="transparent",
                    disabled=ChatState.is_processing,
                    _focus={"outline": "none", "border_color": rx.color("blue", 8)},
                ),
                rx.button(
                    rx.cond(
                        ChatState.is_processing,
                        rx.spinner(size="1"),
                        rx.icon("send", size=20),
                    ),
                    on_click=ChatState.send_message,
                    disabled=ChatState.is_processing | (ChatState.current_input == ""),
                    width="3rem",
                    height="3rem",
                    min_width="3rem",
                    padding="0",
                    border_radius="50%",
                    background_color=rx.color("blue", 9),
                    color="white",
                    _hover={"background_color": rx.color("blue", 10)},
                    _disabled={"background_color": rx.color("gray", 6)},
                ),
                spacing="3",
                width="100%",
            ),
            width="100%",
            max_width="700px",
            margin="0 auto",
        ),
        width="100%",
        padding="1rem 1.5rem",
        border_top="1px solid",
        border_color=rx.color("gray", 4),
        background_color=rx.color("gray", 1),
    )

"""Session sidebar component - displays list of chat sessions."""

import reflex as rx

from ...state import MultiSessionState, ChatState


def new_chat_button() -> rx.Component:
    """Button to create a new chat session."""
    return rx.button(
        rx.icon("plus", size=16),
        rx.text("New Chat"),
        on_click=MultiSessionState.new_session,
        variant="soft",
        width="100%",
        justify="start",
    )


def session_item(session: dict) -> rx.Component:
    """Render a single session item in the list."""
    return rx.box(
        rx.hstack(
            rx.vstack(
                rx.text(
                    session["title"],
                    font_size="0.875rem",
                    font_weight=rx.cond(session["is_current"], "600", "400"),
                    overflow="hidden",
                    text_overflow="ellipsis",
                    white_space="nowrap",
                    max_width="160px",
                ),
                rx.text(
                    session["preview"],
                    font_size="0.75rem",
                    color="gray",
                    overflow="hidden",
                    text_overflow="ellipsis",
                    white_space="nowrap",
                    max_width="160px",
                ),
                spacing="0",
                align_items="start",
                flex="1",
            ),
            rx.vstack(
                rx.text(
                    session["time_ago"],
                    font_size="0.625rem",
                    color="gray",
                ),
                rx.icon_button(
                    rx.icon("trash-2", size=12),
                    on_click=lambda: MultiSessionState.delete_session(session["session_id"]),
                    variant="ghost",
                    size="1",
                    color_scheme="red",
                ),
                spacing="1",
                align_items="end",
            ),
            width="100%",
            justify="between",
        ),
        on_click=lambda: MultiSessionState.switch_session(session["session_id"]),
        padding="8px 12px",
        border_radius="6px",
        cursor="pointer",
        background_color=rx.cond(
            session["is_current"],
            rx.color("blue", 3),
            "transparent",
        ),
        _hover={
            "background_color": rx.cond(
                session["is_current"],
                rx.color("blue", 4),
                rx.color("gray", 3),
            ),
        },
        width="100%",
    )


def session_list() -> rx.Component:
    """Render the list of sessions."""
    return rx.cond(
        MultiSessionState.is_loading_sessions,
        rx.center(
            rx.spinner(size="2"),
            padding="20px",
        ),
        rx.cond(
            MultiSessionState.sessions.length() > 0,
            rx.vstack(
                rx.foreach(
                    MultiSessionState.sessions,
                    session_item,
                ),
                spacing="1",
                width="100%",
                padding="8px",
                overflow_y="auto",
                flex="1",
            ),
            rx.center(
                rx.vstack(
                    rx.icon("message-square-dashed", size=32, color="gray"),
                    rx.text("No sessions yet", color="gray", font_size="0.875rem"),
                    rx.text(
                        "Start a new chat to begin",
                        color="gray",
                        font_size="0.75rem",
                    ),
                    spacing="2",
                    align="center",
                ),
                padding="40px 20px",
                flex="1",
            ),
        ),
    )


def session_sidebar() -> rx.Component:
    """Render the session sidebar."""
    return rx.cond(
        MultiSessionState.show_session_sidebar,
        rx.box(
            # Header
            rx.hstack(
                rx.hstack(
                    rx.icon("messages-square", size=20, color=rx.color("blue", 9)),
                    rx.text("Chats", font_weight="600", font_size="14px"),
                    spacing="2",
                ),
                rx.icon_button(
                    rx.icon("panel-left-close", size=16),
                    on_click=MultiSessionState.toggle_sidebar,
                    variant="ghost",
                    size="1",
                ),
                justify="between",
                width="100%",
                padding="12px",
                border_bottom="1px solid",
                border_color=rx.color("gray", 4),
            ),
            # New chat button
            rx.box(
                new_chat_button(),
                padding="8px 12px",
                border_bottom="1px solid",
                border_color=rx.color("gray", 4),
            ),
            # Session list
            session_list(),
            # Sidebar container styles
            width="220px",
            min_width="220px",
            height="100vh",
            position="fixed",
            left="0",
            top="0",
            background_color=rx.color("gray", 2),
            border_right="1px solid",
            border_color=rx.color("gray", 4),
            display="flex",
            flex_direction="column",
            z_index="99",
            on_mount=MultiSessionState.load_sessions,
        ),
    )


def session_sidebar_toggle() -> rx.Component:
    """Toggle button when session sidebar is closed."""
    return rx.cond(
        ~MultiSessionState.show_session_sidebar,
        rx.icon_button(
            rx.icon("messages-square", size=18),
            on_click=MultiSessionState.toggle_sidebar,
            variant="ghost",
            size="2",
        ),
    )
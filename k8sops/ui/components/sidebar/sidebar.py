"""Unified sidebar component - header, session list, and settings."""

import reflex as rx

from ...state import ChatState, BaseState, MultiSessionState
from ...state.settings import SettingsState
from ...styles import WARM_BG_SIDEBAR


def settings_popover() -> rx.Component:
    """Settings popover with provider and model selection."""
    return rx.popover.root(
        rx.popover.trigger(
            rx.button(
                rx.icon("settings", size=16),
                rx.text("Settings"),
                variant="ghost",
                width="100%",
                justify="start",
            ),
        ),
        rx.popover.content(
            rx.vstack(
                # Theme toggle
                rx.hstack(
                    rx.text("Theme", font_size="0.875rem", font_weight="500"),
                    rx.spacer(),
                    rx.icon_button(
                        rx.color_mode_cond(
                            rx.icon("moon", size=14),
                            rx.icon("sun", size=14),
                        ),
                        on_click=rx.toggle_color_mode,
                        variant="ghost",
                        size="1",
                    ),
                    width="100%",
                ),
                rx.divider(margin_y="0.5rem"),
                # Provider selection
                rx.box(
                    rx.text("Provider", font_size="0.875rem", font_weight="500", margin_bottom="0.5rem"),
                    rx.select.root(
                        rx.select.trigger(placeholder="Select provider..."),
                        rx.select.content(
                            rx.select.item("Anthropic", value="anthropic"),
                            rx.select.item("OpenAI", value="openai"),
                            rx.select.item("Ollama", value="ollama"),
                        ),
                        value=SettingsState.llm_provider,
                        on_change=SettingsState.set_provider,
                    ),
                    width="100%",
                ),
                # Model selection - dynamic based on provider
                rx.box(
                    rx.text("Model", font_size="0.875rem", font_weight="500", margin_bottom="0.5rem"),
                    rx.select.root(
                        rx.select.trigger(placeholder="Select model..."),
                        rx.select.content(
                            rx.foreach(
                                SettingsState.available_models,
                                lambda model: rx.select.item(model, value=model),
                            ),
                        ),
                        value=SettingsState.model_name,
                        on_change=SettingsState.set_model_name,
                    ),
                    width="100%",
                ),
                # Temperature slider
                rx.box(
                    rx.hstack(
                        rx.text("Temperature", font_size="0.875rem", font_weight="500"),
                        rx.spacer(),
                        rx.text(SettingsState.temperature, font_size="0.875rem", color="gray"),
                    ),
                    rx.slider(
                        value=[SettingsState.temperature],
                        min=0,
                        max=1,
                        step=0.1,
                        on_change=lambda val: SettingsState.set_temperature(val[0]),
                    ),
                    width="100%",
                    margin_top="0.5rem",
                ),
                # Divider
                rx.divider(margin_y="0.5rem"),
                # Current model display
                rx.hstack(
                    rx.text("Active Model", font_size="0.875rem"),
                    rx.spacer(),
                    rx.text(
                        ChatState.current_model,
                        font_size="0.75rem",
                        color="gray",
                        max_width="150px",
                        overflow="hidden",
                        text_overflow="ellipsis",
                    ),
                    width="100%",
                ),
                # Connection status
                rx.hstack(
                    rx.text("MCP Connected", font_size="0.875rem"),
                    rx.spacer(),
                    rx.cond(
                        ChatState.mcp_connected,
                        rx.icon("circle-check", size=16, color="green"),
                        rx.icon("circle-x", size=16, color="red"),
                    ),
                    width="100%",
                ),
                rx.hstack(
                    rx.text("Agent Ready", font_size="0.875rem"),
                    rx.spacer(),
                    rx.cond(
                        ChatState.agent_ready,
                        rx.icon("circle-check", size=16, color="green"),
                        rx.icon("circle-x", size=16, color="red"),
                    ),
                    width="100%",
                ),
                spacing="3",
                width="280px",
                padding="4px",
            ),
            side="top",
            align="start",
        ),
    )


def session_item_menu(session: dict) -> rx.Component:
    """Dropdown menu for session actions."""
    return rx.menu.root(
        rx.menu.trigger(
            rx.icon_button(
                rx.icon("ellipsis", size=14),
                variant="ghost",
                size="1",
            ),
        ),
        rx.menu.content(
            rx.menu.item(
                rx.hstack(
                    rx.icon("pencil", size=14),
                    rx.text("Rename"),
                    spacing="2",
                ),
                on_click=lambda: MultiSessionState.start_rename(session["session_id"]),
            ),
            rx.menu.item(
                rx.hstack(
                    rx.icon("trash-2", size=14),
                    rx.text("Delete"),
                    spacing="2",
                ),
                color="red",
                on_click=lambda: MultiSessionState.start_delete(session["session_id"]),
            ),
            size="1",
        ),
    )


def session_title_display(session: dict) -> rx.Component:
    """Display session title - either as text or editable input."""
    return rx.cond(
        MultiSessionState.editing_session_id == session["session_id"],
        # Editing mode - show input with save/cancel buttons
        rx.hstack(
            rx.input(
                value=MultiSessionState.editing_title,
                on_change=MultiSessionState.set_editing_title,
                on_key_down=MultiSessionState.handle_rename_key,
                size="1",
                width="100%",
                auto_focus=True,
            ),
            rx.icon_button(
                rx.icon("check", size=12),
                on_click=MultiSessionState.confirm_rename,
                variant="ghost",
                size="1",
                color_scheme="green",
            ),
            rx.icon_button(
                rx.icon("x", size=12),
                on_click=MultiSessionState.cancel_rename,
                variant="ghost",
                size="1",
                color_scheme="gray",
            ),
            spacing="1",
            width="100%",
        ),
        # Display mode - show text
        rx.text(
            session["title"],
            font_size="0.875rem",
            font_weight=rx.cond(session["is_current"], "600", "400"),
            overflow="hidden",
            text_overflow="ellipsis",
            white_space="nowrap",
            max_width="160px",
        ),
    )


def session_item(session: dict) -> rx.Component:
    """Render a single session item in the list."""
    return rx.box(
        rx.hstack(
            rx.vstack(
                session_title_display(session),
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
                session_item_menu(session),
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


def delete_confirmation_dialog() -> rx.Component:
    """Delete confirmation dialog."""
    return rx.alert_dialog.root(
        rx.alert_dialog.content(
            rx.alert_dialog.title("Delete Session"),
            rx.alert_dialog.description(
                rx.vstack(
                    rx.text("Are you sure you want to delete this session?"),
                    rx.text(
                        MultiSessionState.delete_confirm_session_title,
                        font_weight="600",
                        color=rx.color("gray", 12),
                    ),
                    rx.text(
                        "This action cannot be undone.",
                        font_size="0.875rem",
                        color=rx.color("gray", 10),
                    ),
                    spacing="2",
                    align_items="start",
                ),
            ),
            rx.hstack(
                rx.alert_dialog.cancel(
                    rx.button(
                        "Cancel",
                        variant="soft",
                        color_scheme="gray",
                        on_click=MultiSessionState.cancel_delete,
                    ),
                ),
                rx.alert_dialog.action(
                    rx.button(
                        "Delete",
                        variant="solid",
                        color_scheme="red",
                        on_click=MultiSessionState.confirm_delete,
                    ),
                ),
                spacing="3",
                justify="end",
                margin_top="16px",
            ),
        ),
        open=MultiSessionState.delete_confirm_session_id != "",
    )


def session_list() -> rx.Component:
    """Render the scrollable list of sessions."""
    return rx.cond(
        MultiSessionState.is_loading_sessions,
        rx.center(
            rx.spinner(size="2"),
            padding="20px",
        ),
        rx.cond(
            MultiSessionState.sessions.length() > 0,
            rx.box(
                rx.foreach(
                    MultiSessionState.sessions,
                    session_item,
                ),
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


def sidebar() -> rx.Component:
    """Render unified sidebar with header, sessions, and settings."""
    return rx.fragment(
        # Delete confirmation dialog (rendered outside sidebar for proper positioning)
        delete_confirmation_dialog(),
        rx.cond(
            BaseState.sidebar_open,
            rx.box(
            # === TOP: Header ===
            rx.vstack(
                # Title row
                rx.hstack(
                    rx.hstack(
                        rx.icon("server", size=24, color=rx.color("blue", 9)),
                        rx.text("K8S Ops", font_weight="bold", font_size="18px"),
                        spacing="2",
                    ),
                    rx.icon_button(
                        rx.icon("panel-left-close", size=18),
                        on_click=BaseState.toggle_sidebar,
                        variant="ghost",
                    ),
                    justify="between",
                    width="100%",
                ),
                # New Chat button
                rx.button(
                    rx.icon("plus", size=16),
                    rx.text("New Chat"),
                    on_click=MultiSessionState.new_session,
                    variant="soft",
                    width="100%",
                    justify="start",
                ),
                padding="12px",
                spacing="3",
                border_bottom="1px solid",
                border_color=rx.color("gray", 4),
            ),
            # === MIDDLE: Session List (scrollable) ===
            session_list(),
            # === BOTTOM: Action buttons ===
            rx.vstack(
                settings_popover(),
                rx.button(
                    rx.icon("download", size=16),
                    rx.text("Save History"),
                    on_click=ChatState.save_history,
                    variant="ghost",
                    width="100%",
                    justify="start",
                ),
                padding="12px",
                spacing="1",
                border_top="1px solid",
                border_color=rx.color("gray", 4),
            ),
            # Sidebar container styles
            width="260px",
            height="100vh",
            position="fixed",
            left="0",
            top="0",
            background_color=WARM_BG_SIDEBAR,
            border_right="1px solid",
            border_color=rx.color("gray", 4),
            display="flex",
            flex_direction="column",
            z_index="100",
            on_mount=MultiSessionState.load_sessions,
            ),
        ),
    )


def sidebar_toggle() -> rx.Component:
    """Toggle button when sidebar is closed."""
    return rx.cond(
        ~BaseState.sidebar_open,
        rx.icon_button(
            rx.icon("panel-left-open", size=18),
            on_click=BaseState.toggle_sidebar,
            variant="ghost",
            position="fixed",
            left="12px",
            top="12px",
            z_index="100",
        ),
    )
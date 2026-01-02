"""UI Design prototype - Chat interface like Claude.ai.

Simple echo app: user input gets echoed back as response.
No backend, just UI layout testing.
"""

import reflex as rx
from typing import TypedDict


class Message(TypedDict):
    """Chat message."""
    role: str  # "user" or "assistant"
    content: str


class State(rx.State):
    """App state."""

    messages: list[Message] = []
    current_input: str = ""
    sidebar_open: bool = True

    # Settings
    selected_model: str = "claude-sonnet"
    api_endpoint: str = "https://api.example.com"

    def set_model(self, value: str):
        """Update selected model."""
        self.selected_model = value

    def set_api_endpoint(self, value: str):
        """Update API endpoint."""
        self.api_endpoint = value

    def set_input(self, value: str):
        """Update input value."""
        self.current_input = value

    def toggle_sidebar(self):
        """Toggle sidebar visibility."""
        self.sidebar_open = not self.sidebar_open

    def clear_chat(self):
        """Clear all messages."""
        self.messages = []

    def send_message(self):
        """Send message and echo it back."""
        if not self.current_input.strip():
            return

        user_msg = self.current_input.strip()

        # Add user message
        self.messages.append({"role": "user", "content": user_msg})

        # Echo back as assistant (simple test)
        self.messages.append({
            "role": "assistant",
            "content": f"You said: {user_msg}"
        })

        # Clear input
        self.current_input = ""

    def handle_key_down(self, key: str):
        """Handle Enter key to submit."""
        if key == "Enter":
            return self.send_message()


def message_bubble(msg: Message) -> rx.Component:
    """Render a single message bubble."""
    return rx.box(
        rx.text(msg["content"]),
        padding="12px 16px",
        border_radius="16px",
        max_width="70%",
        background_color=rx.cond(
            msg["role"] == "user",
            rx.color("blue", 9),
            rx.color("gray", 4),
        ),
        color=rx.cond(
            msg["role"] == "user",
            "white",
            rx.color("gray", 12),
        ),
        align_self=rx.cond(
            msg["role"] == "user",
            "flex-end",
            "flex-start",
        ),
    )


def chat_messages() -> rx.Component:
    """Render scrollable message list, centered."""
    return rx.auto_scroll(
        rx.box(
            rx.foreach(State.messages, message_bubble),
            width="100%",
            max_width="700px",
            margin="0 auto",
            display="flex",
            flex_direction="column",
            gap="12px",
        ),
        flex="1",
        padding="16px 24px",
        width="100%",
    )


def input_bar() -> rx.Component:
    """Render fixed input bar at bottom, centered."""
    return rx.box(
        rx.box(
            rx.hstack(
                rx.input(
                    value=State.current_input,
                    on_change=State.set_input,
                    on_key_down=State.handle_key_down,
                    placeholder="Ask about your Kubernetes cluster...",
                    width="100%",
                    height="3rem",
                    padding_x="1rem",
                    font_size="1rem",
                    border_radius="1.5rem",
                    border="1px solid",
                    border_color=rx.color("gray", 6),
                    background="transparent",
                    _focus={"outline": "none", "border_color": rx.color("blue", 8)},
                ),
                rx.button(
                    rx.icon("send", size=20),
                    on_click=State.send_message,
                    disabled=State.current_input == "",
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


def settings_popover() -> rx.Component:
    """Settings popover with dropdown and text input."""
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
                # Model selection dropdown
                rx.box(
                    rx.text("Model", font_size="0.875rem", font_weight="500", margin_bottom="0.5rem"),
                    rx.select.root(
                        rx.select.trigger(placeholder="Select model..."),
                        rx.select.content(
                            rx.select.item("Claude Sonnet", value="claude-sonnet"),
                            rx.select.item("Claude Opus", value="claude-opus"),
                            rx.select.item("Claude Haiku", value="claude-haiku"),
                            rx.select.item("GPT-4", value="gpt-4"),
                            rx.select.item("GPT-3.5", value="gpt-3.5"),
                        ),
                        value=State.selected_model,
                        on_change=State.set_model,
                    ),
                    width="100%",
                ),
                # API Endpoint text input
                rx.box(
                    rx.text("API Endpoint", font_size="0.875rem", font_weight="500", margin_bottom="0.5rem"),
                    rx.input(
                        value=State.api_endpoint,
                        on_change=State.set_api_endpoint,
                        placeholder="https://api.example.com",
                        width="100%",
                    ),
                    width="100%",
                ),
                # Divider
                rx.divider(margin_y="0.5rem"),
                # Additional options
                rx.hstack(
                    rx.text("Theme", font_size="0.875rem"),
                    rx.spacer(),
                    rx.switch(default_checked=True),
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


def sidebar() -> rx.Component:
    """Render fixed sidebar."""
    return rx.cond(
        State.sidebar_open,
        rx.box(
            # Header
            rx.hstack(
                rx.hstack(
                    rx.icon("message-square", size=24),
                    rx.text("K8S Ops Agent", font_weight="bold", font_size="18px"),
                    spacing="2",
                ),
                rx.icon_button(
                    rx.icon("panel-left-close", size=18),
                    on_click=State.toggle_sidebar,
                    variant="ghost",
                ),
                justify="between",
                width="100%",
                padding="16px",
                border_bottom="1px solid",
                border_color=rx.color("gray", 4),
            ),
            # Spacer
            rx.box(flex="1"),
            # Bottom buttons
            rx.vstack(
                settings_popover(),
                rx.button(
                    rx.icon("trash-2", size=16),
                    rx.text("Clear Chat"),
                    on_click=State.clear_chat,
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
            width="240px",
            height="100vh",
            position="fixed",
            left="0",
            top="0",
            background_color=rx.color("gray", 2),
            border_right="1px solid",
            border_color=rx.color("gray", 4),
            display="flex",
            flex_direction="column",
            z_index="100",
        ),
    )


def sidebar_toggle() -> rx.Component:
    """Toggle button when sidebar is closed."""
    return rx.cond(
        ~State.sidebar_open,
        rx.icon_button(
            rx.icon("panel-left-open", size=18),
            on_click=State.toggle_sidebar,
            variant="ghost",
            position="fixed",
            left="12px",
            top="12px",
            z_index="100",
        ),
    )


def chat_area() -> rx.Component:
    """Main chat area."""
    return rx.vstack(
        # Messages (scrollable, takes remaining space)
        chat_messages(),
        # Input bar (fixed at bottom)
        input_bar(),
        height="100vh",
        width="100%",
        spacing="0",
    )


def index() -> rx.Component:
    """Main page layout."""
    return rx.box(
        # Fixed sidebar
        sidebar(),
        # Toggle button
        sidebar_toggle(),
        # Main content (offset by sidebar width)
        rx.box(
            chat_area(),
            margin_left=rx.cond(State.sidebar_open, "240px", "0"),
            transition="margin-left 0.2s ease",
            height="100vh",
        ),
        background_color=rx.color("gray", 1),
        color=rx.color("gray", 12),
        min_height="100vh",
    )


# Create app
app = rx.App(
    theme=rx.theme(
        appearance="dark",
        accent_color="blue",
    ),
)
app.add_page(index)

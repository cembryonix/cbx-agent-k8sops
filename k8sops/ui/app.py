"""K8SOps - Reflex UI application."""

import reflex as rx
from .pages import index
from .styles import base_style


# Create the app
app = rx.App(
    style=base_style,
    theme=rx.theme(
        appearance="dark",
        accent_color="blue",
        radius="medium",
    ),
)

# Add pages
app.add_page(index, route="/", title="K8SOps")

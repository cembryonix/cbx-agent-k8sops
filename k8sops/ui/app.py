"""K8SOps - Reflex UI application."""

import logging
import os

import reflex as rx
from .pages import index
from .styles import base_style

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

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

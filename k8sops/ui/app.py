"""K8SOps - Reflex UI application."""

import logging

import reflex as rx

from k8sops.config import get_app_settings
from .pages import index
from .styles import base_style

# Configure logging
app_settings = get_app_settings()
log_level = app_settings.log_level.upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Create the app
app = rx.App(
    style=base_style,
    theme=rx.theme(
        appearance="light",
        accent_color="blue",
        gray_color="sand",  # Warm, yellowish gray for cream-like light theme
        radius="medium",
    ),
)

# Add pages
app.add_page(index, route="/", title="K8SOps")

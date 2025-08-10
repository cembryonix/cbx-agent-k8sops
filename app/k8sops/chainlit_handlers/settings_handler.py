# chainlit_handlers/settings_handler.py

import chainlit as cl
from typing import Dict, Any

from .session_handler import reinitialize_model_and_agent

from ..utils import get_logger

logger = get_logger(__name__)


async def handle_settings_update(settings: Dict[str, Any], default_config) -> None:
    """Handle settings updates - reinitialize agent if needed."""

    if not validate_settings(settings):
        await cl.Message(content="❌ Invalid settings provided").send()
        return

    try:
        current_settings = get_current_settings()
        logger.info(f"Settings update requested: {settings}")
        logger.debug(f"Current settings: {current_settings}")

        # Check if agent reinitialization is needed
        if _settings_changed(settings, current_settings):
            await reinitialize_model_and_agent(settings)
        else:
            await cl.Message(content="✅ Settings updated!").send()

    except Exception as e:
        logger.error(f"Failed to handle settings update: {e}")
        await cl.Message(content=f"❌ Failed to update settings: {str(e)}").send()
        raise


def _settings_changed(new_settings: Dict[str, Any], current_settings: Dict[str, Any]) -> bool:
    """Check if settings have changed in a way that requires reinitialization."""
    return (new_settings["model"] != current_settings["model"] or
            new_settings["temperature"] != current_settings["temperature"])


def get_current_settings() -> Dict[str, Any]:
    """Get current settings from user session."""
    llm_provider = cl.user_session.get('llm_provider', '')
    llm_model_name = cl.user_session.get('llm_model_name', '')
    current_model = f"{llm_provider}/{llm_model_name}" if llm_provider and llm_model_name else ""

    return {
        "model": current_model,
        "temperature": cl.user_session.get("temperature", 0.1)
    }


def validate_settings(settings: Dict[str, Any]) -> bool:
    """Validate settings before applying them."""
    required_keys = ["model", "temperature"]

    # Check required keys exist
    if not all(key in settings for key in required_keys):
        logger.warning(f"Missing required settings keys: {required_keys}")
        return False

    # Validate temperature range
    try:
        temp = float(settings["temperature"])
        if not (0.0 <= temp <= 2.0):
            logger.warning(f"Temperature {temp} out of valid range [0.0, 2.0]")
            return False
    except (ValueError, TypeError):
        logger.warning(f"Invalid temperature value: {settings['temperature']}")
        return False

    # Validate model format
    if not isinstance(settings["model"], str) or not settings["model"].strip():
        logger.warning(f"Invalid model value: {settings['model']}")
        return False

    if "/" not in settings["model"]:
        logger.warning(f"Model must be in 'provider/model' format: {settings['model']}")
        return False

    return True

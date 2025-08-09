# chainlit_handlers/settings_handler.py

import chainlit as cl
from typing import Dict, Any
from ..models import initialize_model, get_provider_config
from ..agent import setup_agent

from ..utils import get_logger
logger = get_logger(__name__)


async def handle_settings_update(settings: Dict[str, Any], default_config) -> None:

    try:
        # Get current settings
        current_model = cl.user_session.get("model")
        current_temp = cl.user_session.get("temperature")

        logger.info(f"Settings update requested: {settings}")
        logger.debug(f"Current model: {current_model}, temp: {current_temp}")

        # Check if agent reinitialization is needed
        if (settings["model"] != current_model or
                settings["temperature"] != current_temp):

            await _reinitialize_agent_with_new_settings(settings, default_config)
        else:
            await cl.Message(content="✅ Settings updated!").send()

    except Exception as e:
        logger.error(f"Failed to handle settings update: {e}")
        await cl.Message(content=f"❌ Failed to update settings: {str(e)}").send()
        raise


async def _reinitialize_agent_with_new_settings(settings: Dict[str, Any], default_config) -> None:

    await cl.Message(content="🔄 Updating agent configuration...").send()

    # Store initial settings in user session
    selected_model = settings['model']
    llm_provider, llm_model_name = selected_model.split("/", 1)

    cl.user_session.set('llm_provider', llm_provider)
    cl.user_session.set('llm_model_name', llm_model_name)
    cl.user_session.set("temperature", settings["temperature"])

    llm_config = get_provider_config(llm_provider,llm_model_name)

    # Init LLM
    try:
        model = await initialize_model(llm_provider, llm_model_name, llm_config)
        cl.user_session.set("model", model)
        await cl.Message(content=f"✅ LLM Model \"{llm_model_name}\" is initialized.").send()
    except Exception as e:
        await cl.Message(content=f"❌ Failed to initialize LLM Model: {str(e)}").send()

    model = cl.user_session.get("model")
    mcp_tools = cl.user_session.get("mcp_tools")

    try:
        agent = await setup_agent(model, mcp_tools)
        cl.user_session.set("agent", agent)
        await cl.Message(
            content=f"✅ Agent updated with {settings['model']} (temp: {settings['temperature']})"
        ).send()

        logger.info(f"Agent successfully reinitialized with settings: {settings}")

    except Exception as e:
        logger.error(f"Agent reinitialization failed: {e}")
        await cl.Message(content=f"❌ Failed to update agent: {str(e)}").send()
        raise


def get_current_settings() -> Dict[str, Any]:

    return {
        "model": cl.user_session.get("model"),
        "temperature": cl.user_session.get("temperature")
    }


def validate_settings(settings: Dict[str, Any]) -> bool:

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

    # Validate model (you can extend this based on your supported models)
    if not isinstance(settings["model"], str) or not settings["model"].strip():
        logger.warning(f"Invalid model value: {settings['model']}")
        return False

    return True
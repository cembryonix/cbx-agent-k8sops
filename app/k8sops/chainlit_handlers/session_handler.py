# chainlit_handlers/session_handler.py

import chainlit as cl
from typing import Dict, Any, Optional

from ..chainlit_ui.components import create_chat_settings
from ..models import initialize_model, get_provider_config
from ..mcp_client import setup_mcp_client, get_updated_tools
from ..agent import setup_agent

from ..utils import get_logger

logger = get_logger(__name__)


async def init_session(default_config):
    """Initialize a new chat session with default configuration."""
    # Store session ID as thread_id
    thread_id = cl.user_session.get('id')
    cl.user_session.set('thread_id', thread_id)

    # Create and send chat settings if not already set
    if cl.user_session.get('llm_provider') is None:
        settings = await create_chat_settings(default_config)
        selected_model = default_config['main_config']['default_model']

        # Store initial settings
        await _store_model_settings(selected_model, settings["temperature"])
        logger.info(f"Current Model: \"{selected_model}\"")

    # Initialize all components
    await _initialize_model_if_needed()
    await _initialize_mcp_if_needed(default_config)
    await _initialize_agent()

    await cl.Message(content="Agent initialized! Ready to chat!").send()


async def _store_model_settings(selected_model: str, temperature: float):
    """Store model settings in user session."""
    llm_provider, llm_model_name = selected_model.split("/", 1)
    cl.user_session.set('llm_provider', llm_provider)
    cl.user_session.set('llm_model_name', llm_model_name)
    cl.user_session.set("temperature", temperature)


async def _initialize_model_if_needed():
    """Initialize LLM model if not already initialized."""
    if cl.user_session.get("model") is not None:
        return

    llm_provider = cl.user_session.get('llm_provider')
    llm_model_name = cl.user_session.get('llm_model_name')
    llm_config = get_provider_config(llm_provider, llm_model_name)

    try:
        model = await initialize_model(llm_provider, llm_model_name, llm_config)
        cl.user_session.set("model", model)
        await cl.Message(content=f"✅ LLM Model \"{llm_model_name}\" is initialized.").send()
    except Exception as e:
        await cl.Message(content=f"❌ Failed to initialize LLM Model: {str(e)}").send()
        raise


async def _initialize_mcp_if_needed(default_config):
    """Initialize MCP client if not already initialized."""
    if cl.user_session.get('mcp_client') is not None:
        return

    mcp_client_config = default_config['mcp_servers']['k8s_mcp']

    try:
        mcp_client = await setup_mcp_client(mcp_client_config)
        cl.user_session.set("mcp_client", mcp_client)
        await cl.Message(content="✅ K8s MCP client is initialized.").send()

        # Retrieve and store MCP tools
        mcp_tools = await get_updated_tools(mcp_client)
        cl.user_session.set("mcp_tools", mcp_tools)
        await cl.Message(content=f"✅ Loaded {len(mcp_tools)} MCP tools.").send()

    except Exception as e:
        await cl.Message(content=f"❌ Failed to initialize MCP client: {str(e)}").send()
        raise


async def _initialize_agent():
    """Initialize agent with current model and MCP tools."""
    model = cl.user_session.get("model")
    mcp_tools = cl.user_session.get("mcp_tools")

    if not model or not mcp_tools:
        raise ValueError("Model and MCP tools must be initialized before agent")

    agent = await setup_agent(model, mcp_tools)
    cl.user_session.set("agent", agent)


async def reinitialize_model_and_agent(settings: Dict[str, Any]) -> None:
    """Reinitialize model and agent with new settings."""
    await cl.Message(content="🔄 Updating agent configuration...").send()

    # Update stored settings
    selected_model = settings['model']
    await _store_model_settings(selected_model, settings["temperature"])

    # Get new config and reinitialize model
    llm_provider = cl.user_session.get('llm_provider')
    llm_model_name = cl.user_session.get('llm_model_name')
    llm_config = get_provider_config(llm_provider, llm_model_name)

    try:
        model = await initialize_model(llm_provider, llm_model_name, llm_config)
        cl.user_session.set("model", model)
        await cl.Message(content=f"✅ LLM Model \"{llm_model_name}\" is initialized.").send()

        # Reinitialize agent with new model
        await _initialize_agent()
        await cl.Message(
            content=f"✅ Agent updated with model {settings['model']} "
        ).send()

        logger.info(f"Agent successfully reinitialized with settings: {settings}")

    except Exception as e:
        logger.error(f"Model/Agent reinitialization failed: {e}")
        await cl.Message(content=f"❌ Failed to update agent: {str(e)}").send()
        raise
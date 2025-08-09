# chainlit_handlers/session_handler.py

import chainlit as cl

from ..chainlit_ui.components import create_chat_settings
from ..models import initialize_model, get_supported_model_ids, get_provider_config
from ..mcp_client import (
    setup_mcp_client,
    get_updated_tools
)

from ..agent import setup_agent

from ..utils import get_logger
logger = get_logger(__name__)

async def init_session(default_config):

    # Store session ID as thread_id
    thread_id = cl.user_session.get('id')
    cl.user_session.set('thread_id', thread_id)

    # Create and send chat settings
    llm_provider = cl.user_session.get('llm_provider', None)
    if llm_provider is None:
        settings = await create_chat_settings(default_config)



        # Store initial settings in user session
        selected_model = default_config['main_config']['default_model']   # settings['model']
        logger.info(f"Current Model: \"{selected_model}\" ")

        llm_provider, llm_model_name = selected_model.split("/", 1)

        cl.user_session.set('llm_provider', llm_provider)
        cl.user_session.set('llm_model_name', llm_model_name)
        cl.user_session.set("temperature", settings["temperature"])
    else:
        llm_provider = cl.user_session.get('llm_provider')
        llm_model_name = cl.user_session.get('llm_model_name')


    llm_config = get_provider_config(llm_provider,llm_model_name)

    try:
        model = await initialize_model(llm_provider, llm_model_name, llm_config)
        cl.user_session.set("model", model)
        await cl.Message(content="✅ LLM Model is initialized.").send()
    except Exception as e:
        await cl.Message(content=f"❌ Failed to initialize LLM Model: {str(e)}").send()
        return

    # Initialize MCP
    mcp_client_config = default_config['mcp_servers']['k8s_mcp']
    # Init MCP client:
    mcp_client = cl.user_session.get('mcp_client', None)
    if mcp_client is None:
        try:
            mcp_client = await setup_mcp_client(mcp_client_config)
            cl.user_session.set("mcp_client", mcp_client)
            await cl.Message(content="✅ K8s MCP client is initialized.").send()
        except Exception as e:
            await cl.Message(content=f"❌ Failed to initialize MCP client: {str(e)}").send()
            return

    # Retrieve and modify MCP Tools
    mcp_tools = await get_updated_tools(mcp_client)
    cl.user_session.set("mcp_tools", mcp_tools)
    await cl.Message(content=f"✅ Loaded {len(mcp_tools)} MCP tools.").send()

    # Initialize Agent
    agent = await setup_agent(model, mcp_tools)
    cl.user_session.set("agent", agent)

    await cl.Message(content="Agent initialized! Ready to chat! ").send()
# chainlit_handlers/cleanup_handler.py

import chainlit as cl
from typing import Optional

from ..utils import get_logger

logger = get_logger(__name__)


async def cleanup_session():
    """Clean up session resources when chat ends."""

    try:
        thread_id = cl.user_session.get('thread_id')

        # Check if cleanup already performed (handles double-triggering)
        if cl.user_session.get('_cleanup_performed'):
            logger.debug(f"Cleanup already performed for session: {thread_id}")
            return

        logger.info(f"Starting cleanup for session: {thread_id}")

        # Mark cleanup as started to prevent double execution
        cl.user_session.set('_cleanup_performed', True)

        # Clean up MCP client connection
        await _cleanup_mcp_client()

        # Clean up model resources (if needed)
        await _cleanup_model()

        # Clean up agent resources
        await _cleanup_agent()

        # Clear session data
        _clear_session_data()

        logger.info(f"Session cleanup completed for: {thread_id}")

    except Exception as e:
        logger.error(f"Error during session cleanup: {e}")


async def _cleanup_mcp_client():
    """Clean up MCP client connection and resources."""
    mcp_client = cl.user_session.get('mcp_client')
    if mcp_client is not None:
        try:
            # Close MCP client connection if it has a close method
            if hasattr(mcp_client, 'close'):
                await mcp_client.close()
            elif hasattr(mcp_client, 'disconnect'):
                await mcp_client.disconnect()

            logger.debug("MCP client connection closed")
        except Exception as e:
            logger.warning(f"Failed to properly close MCP client: {e}")


async def _cleanup_model():
    """Clean up model resources if needed."""
    model = cl.user_session.get('model')
    if model is not None:
        try:
            # Some models might have cleanup methods
            if hasattr(model, 'close'):
                await model.close()
            elif hasattr(model, 'cleanup'):
                await model.cleanup()

            logger.debug("Model resources cleaned up")
        except Exception as e:
            logger.warning(f"Failed to properly cleanup model: {e}")


async def _cleanup_agent():
    """Clean up agent resources."""
    agent = cl.user_session.get('agent')
    if agent is not None:
        try:
            # LangGraph agents might have cleanup methods
            if hasattr(agent, 'cleanup'):
                await agent.cleanup()
            elif hasattr(agent, 'close'):
                await agent.close()

            logger.debug("Agent resources cleaned up")
        except Exception as e:
            logger.warning(f"Failed to properly cleanup agent: {e}")


def _clear_session_data():
    """Clear all application-specific session data to prevent memory leaks.

    Note: Chainlit doesn't provide a method to get all keys, so we explicitly
    list the keys we manage. This is the standard practice in the Chainlit community.
    System-managed keys (id, env, chat_settings, user, chat_profile) are left intact.
    """
    # TODO: move to global default_config for key validation when doing "set"
    # Application-specific keys we manage
    app_session_keys = [
        'thread_id',
        'llm_provider',
        'llm_model_name',
        'temperature',
        'model',
        'mcp_client',
        'mcp_tools',
        'agent',
        '_cleanup_performed'  # Our cleanup flag
    ]

    cleared_count = 0
    for key in app_session_keys:
        if cl.user_session.get(key) is not None:
            cl.user_session.set(key, None)
            cleared_count += 1

    logger.debug(f"Session data cleared: {cleared_count} keys")


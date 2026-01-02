# mcp_client/server_manager.py

from typing import List, Dict
from langchain_core.tools import BaseTool

from ..utils import get_logger
logger = get_logger(__name__)


async def get_updated_tools(mcp_client, server_key="k8s") -> List[BaseTool]:
    """Retrieve tools from MCP client and update context with extra info.
     return empty list on error"""
    if mcp_client is None:
        logger.error(f"MCP client is None - connection was not established for '{server_key}'")
        return []

    try:
        # Use client.get_tools() instead of session to keep connection alive
        # This way tools can execute properly without ClosedResourceError
        tools = await mcp_client.get_tools()
        return tools
    except Exception as e:
        logger.error(f"Failed to retrieve MCP tools from '{server_key}': {e}")
        return []

    # updated_tools = []
    #
    # for tool in original_tools:
    #     # TODO: future update tools description from outside of MCP standard descriptions
    #     pass
    #
    # return updated_tools

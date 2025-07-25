
from typing import List, Dict
from langchain_core.tools import BaseTool


async def get_updated_tools(mcp_client) -> List[BaseTool]:

    # Get original tools from MCP client
    original_tools = await mcp_client.get_tools()

    # updated_tools = []
    #
    # for tool in original_tools:
    #     # TODO: future update tools description from outside of MCP standard descriptions
    #     pass
    #
    # return updated_tools
    return original_tools
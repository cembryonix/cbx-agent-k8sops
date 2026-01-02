# mcp_client/mcp_client.py

from langchain_mcp_adapters.client import MultiServerMCPClient

from ..utils import get_logger
logger = get_logger(__name__)

async def setup_mcp_client(mcp_config, server_key="k8s"):
    """Initialize the MCP client and verify connectivity."""
    try:
        mcp_client = MultiServerMCPClient({server_key: mcp_config})
        # Test connectivity to specific server using session
        async with mcp_client.session(server_key) as session:
            # This will test if this specific server is reachable
            pass
        return mcp_client
    except Exception as e:
        logger.error(f"Failed to initialize MCP client for '{server_key}': {e}")
        return None
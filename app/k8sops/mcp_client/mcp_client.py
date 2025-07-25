
from langchain_mcp_adapters.client import MultiServerMCPClient

from ..utils import get_logger

logger = get_logger(__name__)

async def setup_mcp_client(mcp_config):
    """Initialize the MCP client"""
    logger.debug(mcp_config)
    k8s_mcp_config = mcp_config
    mcp_client = MultiServerMCPClient({"k8s": k8s_mcp_config})

    return mcp_client
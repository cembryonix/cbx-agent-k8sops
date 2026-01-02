"""Fixtures for integration tests requiring MCP server."""

import os
import pytest
import pytest_asyncio

# Default MCP server URL
DEFAULT_MCP_URL = "https://cbx-mcp-k8s.vvklab.cloud.cembryonix.com/mcp"


@pytest.fixture
def mcp_url():
    """Get MCP server URL from environment or use default."""
    return os.getenv("MCP_SERVER_URL", DEFAULT_MCP_URL)


@pytest.fixture
def ssl_verify():
    """Get SSL verification setting."""
    return os.getenv("MCP_SSL_VERIFY", "false").lower() != "false"


@pytest_asyncio.fixture
async def mcp_client(mcp_url, ssl_verify):
    """Create and connect an MCP client."""
    from k8sops.mcp_client import MCPClient

    client = MCPClient(server_url=mcp_url, ssl_verify=ssl_verify)
    await client.connect()
    yield client
    await client.disconnect()

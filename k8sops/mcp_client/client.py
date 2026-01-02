"""MCP client with dynamic tool discovery.

This module provides a clean async context manager for MCP server connections,
supporting both stdio and streamable HTTP transports.
"""

import logging
import asyncio
from typing import Any
from contextlib import asynccontextmanager

import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_core.tools import BaseTool

from k8sops.config import get_mcp_settings

logger = logging.getLogger(__name__)


def create_insecure_httpx_client(**kwargs) -> httpx.AsyncClient:
    """Create an httpx client that skips SSL verification.

    Accepts all kwargs that httpx.AsyncClient accepts, but forces verify=False.
    """
    kwargs["verify"] = False
    return httpx.AsyncClient(**kwargs)


class MCPClient:
    """MCP client with dynamic tool discovery.

    Connects to a single MCP server and discovers available tools dynamically.
    Supports both stdio (local) and HTTP (remote) transports.
    """

    def __init__(self, server_url: str | None = None, transport: str | None = None, ssl_verify: bool | None = None):
        """Initialize MCP client.

        Args:
            server_url: MCP server URL (for HTTP transport) or None to use settings
            transport: Transport type ('stdio' or 'http') or None to use settings
            ssl_verify: Whether to verify SSL certificates (None to use settings)
        """
        settings = get_mcp_settings()
        self.transport = transport or settings.transport
        self.server_url = server_url or settings.server_url
        self.ssl_verify = ssl_verify if ssl_verify is not None else settings.ssl_verify
        self.stdio_command = settings.command
        self.stdio_args = settings.get_stdio_args()

        self.session: ClientSession | None = None
        self._tools: list[dict] = []
        self._langchain_tools: list[BaseTool] = []
        self._connection_task: asyncio.Task | None = None
        self._stop_event: asyncio.Event | None = None
        self._ready_event: asyncio.Event | None = None
        self._error: Exception | None = None

    async def connect(self) -> list[dict]:
        """Connect to MCP server and discover tools.

        Returns:
            List of discovered tool definitions
        """
        self._stop_event = asyncio.Event()
        self._ready_event = asyncio.Event()
        self._error = None

        # Start connection in a dedicated task to keep context consistent
        self._connection_task = asyncio.create_task(self._run_connection())

        # Wait for connection to be ready or error
        await self._ready_event.wait()

        if self._error:
            raise self._error

        return self._tools

    async def _run_connection(self):
        """Run the MCP connection in a dedicated task."""
        try:
            if self.transport == "stdio":
                await self._run_stdio_connection()
            else:
                await self._run_http_connection()
        except Exception as e:
            logger.error(f"MCP connection error: {e}")
            self._error = e
            self._ready_event.set()

    async def _run_stdio_connection(self):
        """Run stdio connection."""
        server_params = StdioServerParameters(
            command=self.stdio_command,
            args=self.stdio_args,
        )
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                self.session = session
                await self._initialize_session()
                self._ready_event.set()
                # Keep connection alive until stop is requested
                await self._stop_event.wait()

    async def _run_http_connection(self):
        """Run HTTP connection."""
        if not self.server_url:
            raise ValueError("MCP_SERVER_URL is required for HTTP transport")

        logger.info(f"Connecting to MCP server at {self.server_url} (ssl_verify={self.ssl_verify})")

        # Build kwargs for streamablehttp_client
        kwargs = {}
        if not self.ssl_verify:
            kwargs["httpx_client_factory"] = create_insecure_httpx_client

        async with streamablehttp_client(self.server_url, **kwargs) as (read, write, _):
            async with ClientSession(read, write) as session:
                self.session = session
                await self._initialize_session()
                self._ready_event.set()
                # Keep connection alive until stop is requested
                await self._stop_event.wait()

    async def _initialize_session(self):
        """Initialize session and discover tools."""
        await self.session.initialize()

        # Discover tools
        self._tools = await self._discover_tools()
        logger.info(f"Discovered {len(self._tools)} tools from MCP server")

        # Pre-load LangChain tools
        self._langchain_tools = await load_mcp_tools(self.session)

    async def disconnect(self):
        """Disconnect from MCP server."""
        if self._stop_event:
            self._stop_event.set()

        if self._connection_task:
            try:
                await asyncio.wait_for(self._connection_task, timeout=5.0)
            except asyncio.TimeoutError:
                self._connection_task.cancel()
                try:
                    await self._connection_task
                except asyncio.CancelledError:
                    pass

        self.session = None
        self._tools = []
        self._langchain_tools = []
        self._connection_task = None
        self._stop_event = None
        self._ready_event = None

    async def _discover_tools(self) -> list[dict]:
        """Discover available tools from MCP server.

        Returns:
            List of tool definitions with name, description, and input schema
        """
        result = await self.session.list_tools()
        return [
            {
                "name": tool.name,
                "description": tool.description or "",
                "input_schema": tool.inputSchema,
            }
            for tool in result.tools
        ]

    @property
    def tools(self) -> list[dict]:
        """Get discovered tool definitions."""
        return self._tools

    def get_langchain_tools(self) -> list[BaseTool]:
        """Get LangChain-compatible tools.

        Returns:
            List of LangChain BaseTool instances
        """
        return self._langchain_tools

    async def call_tool(self, name: str, arguments: dict) -> str:
        """Execute a tool by name.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            Tool execution result as string
        """
        if not self.session:
            raise RuntimeError("Not connected to MCP server")

        result = await self.session.call_tool(name, arguments)

        # Extract text content from result
        if result.content:
            return result.content[0].text if hasattr(result.content[0], "text") else str(result.content[0])
        return ""


@asynccontextmanager
async def create_mcp_client(
    server_url: str | None = None,
    transport: str | None = None,
):
    """Create an MCP client as an async context manager.

    Args:
        server_url: MCP server URL (for HTTP transport)
        transport: Transport type ('stdio' or 'http')

    Yields:
        Connected MCPClient instance

    Example:
        async with create_mcp_client() as client:
            tools = client.get_langchain_tools()
    """
    client = MCPClient(server_url=server_url, transport=transport)
    try:
        await client.connect()
        yield client
    finally:
        await client.disconnect()

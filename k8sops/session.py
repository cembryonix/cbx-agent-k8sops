"""Core session management for K8S Ops Agent.

AgentSession is the core class that manages an agent conversation session.
It's independent of any UI framework (Reflex, CLI, etc.) and can be used
by any interface.
"""

import logging
import uuid
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Literal

logger = logging.getLogger(__name__)


@dataclass
class SessionSettings:
    """Settings for an agent session."""

    provider: Literal["anthropic", "openai", "ollama"] = "anthropic"
    model_name: str = "claude-sonnet-4-20250514"
    temperature: float = 0.0

    # MCP settings
    mcp_server_url: str | None = None
    mcp_transport: Literal["stdio", "http"] = "http"
    mcp_ssl_verify: bool = False

    @classmethod
    def from_env(cls) -> "SessionSettings":
        """Create settings from environment variables."""
        from k8sops.config import get_llm_settings, get_mcp_settings

        llm = get_llm_settings()
        mcp = get_mcp_settings()

        return cls(
            provider=llm.provider,
            model_name=llm.model_name,
            temperature=0.0,
            mcp_server_url=mcp.server_url,
            mcp_transport=mcp.transport,
            mcp_ssl_verify=mcp.ssl_verify,
        )

    def model_key(self) -> str:
        """Return a key representing the current model config."""
        return f"{self.provider}/{self.model_name}/{self.temperature}"


@dataclass
class Message:
    """A chat message."""

    role: str  # "user" or "assistant"
    content: str


@dataclass
class ToolCall:
    """A tool call record."""

    id: str
    name: str
    arguments: str = ""
    status: str = "pending"  # "pending", "running", "complete", "error"
    output: str = ""
    error: str = ""


class AgentSession:
    """
    Core session management for an agent conversation.

    This class is UI-agnostic and can be used by Reflex UI, CLI, or tests.
    It manages:
    - Session settings (provider, model, temperature)
    - MCP client connection
    - LangGraph agent
    - Conversation state (messages, tool calls)
    """

    def __init__(
        self,
        session_id: str | None = None,
        settings: SessionSettings | None = None,
    ):
        """Initialize a new agent session.

        Args:
            session_id: Unique session identifier. Generated if not provided.
            settings: Session settings. Loaded from env if not provided.
        """
        self.session_id = session_id or str(uuid.uuid4())
        self.settings = settings or SessionSettings.from_env()

        # State
        self.messages: list[Message] = []
        self.tool_calls: list[ToolCall] = []
        self.available_tools: list[dict] = []

        # Components (initialized lazily)
        self._mcp_client: Any = None
        self._agent: Any = None
        self._checkpointer: Any = None  # Preserved across model switches
        self._thread_id: str = self.session_id
        self._model_key: str = ""

        # Status
        self.mcp_connected: bool = False
        self.agent_ready: bool = False
        self.is_processing: bool = False
        self.is_streaming: bool = False
        self.error_message: str = ""

    async def initialize(self) -> None:
        """Initialize MCP client and agent."""
        if self.agent_ready:
            return

        self.is_processing = True
        self.error_message = ""

        try:
            await self._connect_mcp()
            await self._create_agent()

            self.messages = [
                Message(
                    role="assistant",
                    content="Connected to K8S MCP server. Ready to help with your cluster!",
                )
            ]
            logger.info(f"Session {self.session_id[:8]}... initialized")

        except Exception as e:
            logger.exception("Failed to initialize session")
            self.error_message = f"Failed to initialize: {str(e)}"
            self.mcp_connected = False
            self.agent_ready = False
            raise

        finally:
            self.is_processing = False

    async def _connect_mcp(self) -> None:
        """Connect to MCP server."""
        from k8sops.mcp_client import MCPClient

        self._mcp_client = MCPClient(
            server_url=self.settings.mcp_server_url,
            transport=self.settings.mcp_transport,
            ssl_verify=self.settings.mcp_ssl_verify,
        )

        tools = await self._mcp_client.connect()
        self.available_tools = tools
        self.mcp_connected = True
        logger.info(f"Connected to MCP, found {len(tools)} tools")

    async def _create_agent(self) -> None:
        """Create LangGraph agent with current settings.

        Preserves the checkpointer across model switches to maintain
        conversation history.
        """
        from k8sops.models import create_model
        from k8sops.agent import create_agent_with_mcp

        model = create_model(
            provider=self.settings.provider,
            model_name=self.settings.model_name,
            temperature=self.settings.temperature,
        )

        # Create checkpointer once, reuse across model switches
        if self._checkpointer is None:
            self._checkpointer = await self._create_checkpointer()

        self._agent = await create_agent_with_mcp(model, self._mcp_client, self._checkpointer)
        self._model_key = self.settings.model_key()
        self.agent_ready = True
        logger.info(f"Created agent with {self.settings.provider}/{self.settings.model_name}")

    async def _create_checkpointer(self) -> Any:
        """Create the appropriate checkpointer based on configuration.

        Returns AsyncRedisSaver if REDIS_URL is configured, otherwise MemorySaver.
        """
        from k8sops.config import get_memory_settings

        memory_settings = get_memory_settings()

        if memory_settings.use_redis:
            from langgraph.checkpoint.redis import AsyncRedisSaver
            from langgraph.checkpoint.redis.ashallow import AsyncShallowRedisSaver

            if memory_settings.shallow:
                logger.info("Using AsyncShallowRedisSaver for persistent memory")
                saver = AsyncShallowRedisSaver(redis_url=memory_settings.redis_url)
            else:
                logger.info("Using AsyncRedisSaver for persistent memory")
                saver = AsyncRedisSaver(redis_url=memory_settings.redis_url)

            await saver.asetup()
            return saver
        else:
            from langgraph.checkpoint.memory import MemorySaver

            logger.info("Using in-memory checkpointer (not persistent)")
            return MemorySaver()

    async def update_settings(self, **kwargs) -> bool:
        """Update session settings and reinitialize agent if needed.

        Args:
            **kwargs: Settings to update (provider, model_name, temperature, etc.)

        Returns:
            True if agent was reinitialized, False if only settings updated.
        """
        old_model_key = self.settings.model_key()

        # Update settings
        for key, value in kwargs.items():
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)

        new_model_key = self.settings.model_key()

        # Reinitialize agent if model config changed
        if old_model_key != new_model_key and self.agent_ready:
            logger.info(f"Model changed from {old_model_key} to {new_model_key}, reinitializing")
            await self._create_agent()
            return True

        return False

    async def send_message(self, content: str) -> AsyncIterator[dict]:
        """Send a message and stream the response.

        Args:
            content: User message content.

        Yields:
            Event dicts with type and data:
            - {"type": "user_message", "content": str}
            - {"type": "token", "content": str}
            - {"type": "tool_start", "tool_call": ToolCall}
            - {"type": "tool_end", "tool_call": ToolCall}
            - {"type": "assistant_message", "content": str}
            - {"type": "error", "message": str}
        """
        if not content.strip():
            return

        if not self.agent_ready:
            yield {"type": "error", "message": "Agent not ready. Please wait for initialization."}
            return

        # Add user message
        user_message = Message(role="user", content=content.strip())
        self.messages.append(user_message)
        yield {"type": "user_message", "content": user_message.content}

        self.is_streaming = True
        self.is_processing = True
        self.tool_calls = []

        # Prepare assistant message
        assistant_content = ""

        try:
            config = {"configurable": {"thread_id": self._thread_id}}

            async for event in self._agent.astream_events(
                {"messages": [{"role": "user", "content": content.strip()}]},
                config=config,
                version="v2",
            ):
                event_type = event.get("event", "")

                # Handle streaming tokens
                if event_type == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk")
                    if chunk and hasattr(chunk, "content") and chunk.content:
                        token_content = self._extract_content(chunk.content)
                        if token_content:
                            assistant_content += token_content
                            yield {"type": "token", "content": token_content}

                # Handle tool start
                elif event_type == "on_tool_start":
                    tool_call = ToolCall(
                        id=event.get("run_id", ""),
                        name=event.get("name", "unknown"),
                        arguments=str(event.get("data", {}).get("input", {})),
                        status="running",
                    )
                    self.tool_calls.append(tool_call)
                    yield {"type": "tool_start", "tool_call": tool_call}

                # Handle tool end
                elif event_type == "on_tool_end":
                    run_id = event.get("run_id", "")
                    output = event.get("data", {}).get("output", "")

                    for tc in self.tool_calls:
                        if tc.id == run_id:
                            tc.status = "complete"
                            tc.output = str(output)
                            yield {"type": "tool_end", "tool_call": tc}
                            break

            # Add assistant message
            self.messages.append(Message(role="assistant", content=assistant_content))
            yield {"type": "assistant_message", "content": assistant_content}

        except Exception as e:
            logger.exception("Error during message processing")
            error_msg = f"Error: {str(e)}"
            self.messages.append(Message(role="assistant", content=error_msg))
            self.error_message = str(e)
            yield {"type": "error", "message": str(e)}

        finally:
            self.is_streaming = False
            self.is_processing = False

    def _extract_content(self, content: Any) -> str:
        """Extract text content from various chunk formats."""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            text_parts = []
            for block in content:
                if isinstance(block, str):
                    text_parts.append(block)
                elif isinstance(block, dict) and block.get("type") == "text":
                    text_parts.append(block.get("text", ""))
            return "".join(text_parts)
        return ""

    def clear_messages(self) -> None:
        """Clear conversation history."""
        self.messages = []
        self.tool_calls = []
        self.error_message = ""

    async def cleanup(self) -> None:
        """Cleanup session resources."""
        if self._mcp_client:
            try:
                await self._mcp_client.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting MCP client: {e}")

        self._mcp_client = None
        self._agent = None
        self.mcp_connected = False
        self.agent_ready = False
        logger.info(f"Session {self.session_id[:8]}... cleaned up")

    def get_current_model(self) -> str:
        """Get current model identifier."""
        return f"{self.settings.provider}/{self.settings.model_name}"

    def to_dict(self) -> dict:
        """Export session state as dict (for serialization)."""
        return {
            "session_id": self.session_id,
            "settings": {
                "provider": self.settings.provider,
                "model_name": self.settings.model_name,
                "temperature": self.settings.temperature,
            },
            "messages": [{"role": m.role, "content": m.content} for m in self.messages],
            "mcp_connected": self.mcp_connected,
            "agent_ready": self.agent_ready,
            "current_model": self.get_current_model(),
        }

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
        self._memory_manager: Any = None  # Long-term memory
        self._session_store: Any = None  # Session metadata store
        self._thread_id: str = self.session_id
        self._model_key: str = ""
        self._model: Any = None  # LLM model reference for memory operations
        self._title_set: bool = False  # Track if title has been set from first message

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
            is_resuming = await self._init_session_store()
            await self._init_memory_manager()

            # Retrieve relevant memories for agent context
            memories = await self._get_memory_context()
            memory_context = ""
            if memories and self._memory_manager:
                memory_context = self._memory_manager.format_memories_for_context(memories)

            await self._create_agent(memory_context=memory_context)

            # Restore conversation history if resuming existing session
            if is_resuming:
                restored = await self._restore_messages_from_checkpointer()
                if restored:
                    self._title_set = True  # Title already set for existing session
                    logger.info(f"Session {self.session_id[:8]}... resumed with history")
                else:
                    # Checkpointer had no messages, treat as new
                    self._set_welcome_message(memories)
                    logger.info(f"Session {self.session_id[:8]}... initialized (no history found)")
            else:
                # New session - show welcome message
                self._set_welcome_message(memories)
                logger.info(f"Session {self.session_id[:8]}... initialized")

        except Exception as e:
            logger.exception("Failed to initialize session")
            self.error_message = f"Failed to initialize: {str(e)}"
            self.mcp_connected = False
            self.agent_ready = False
            raise

        finally:
            self.is_processing = False

    def _set_welcome_message(self, memories: list[dict] | None = None) -> None:
        """Set the welcome message for a new session."""
        welcome_msg = "Connected to K8S MCP server. Ready to help with your cluster!"
        if memories:
            welcome_msg += f"\n\n[Retrieved {len(memories)} relevant memories from previous sessions]"
        self.messages = [Message(role="assistant", content=welcome_msg)]

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

    async def _init_session_store(self) -> bool:
        """Initialize session store for metadata tracking.

        Returns:
            True if resuming an existing session, False if new session.
        """
        from k8sops.config import get_memory_settings, get_app_settings
        from k8sops.session.store import SessionStore

        memory_settings = get_memory_settings()
        app_settings = get_app_settings()

        if not memory_settings.use_redis:
            logger.debug("Redis not configured, session store disabled")
            return False

        self._session_store = SessionStore(
            redis_url=memory_settings.redis_url,
            user_id=memory_settings.user_id,
        )

        # Check if session exists (resuming) or create new
        if await self._session_store.session_exists(self.session_id):
            logger.info(f"Resuming existing session {self.session_id[:8]}...")
            # Update timestamp on resume
            await self._session_store.update_session(self.session_id)
            return True
        else:
            # Create new session
            await self._session_store.create_session(self.session_id)
            # Enforce session limit
            await self._session_store.enforce_session_limit(app_settings.max_sessions)
            logger.info(f"Created new session {self.session_id[:8]}...")
            return False

    def _create_model(self) -> None:
        """Create the LLM model if not already created."""
        if self._model is not None:
            return

        from k8sops.models import create_model

        self._model = create_model(
            provider=self.settings.provider,
            model_name=self.settings.model_name,
            temperature=self.settings.temperature,
        )

    async def _create_agent(self, memory_context: str = "") -> None:
        """Create LangGraph agent with current settings.

        Preserves the checkpointer across model switches to maintain
        conversation history.

        Args:
            memory_context: Optional context from long-term memory.
        """
        from k8sops.agent import create_agent_with_mcp

        self._create_model()

        # Create checkpointer once, reuse across model switches
        if self._checkpointer is None:
            self._checkpointer = await self._create_checkpointer()

        self._agent = await create_agent_with_mcp(
            self._model, self._mcp_client, self._checkpointer, memory_context
        )
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

    async def _restore_messages_from_checkpointer(self) -> bool:
        """Restore conversation messages from the checkpointer.

        Returns:
            True if messages were restored, False otherwise.
        """
        if not self._checkpointer:
            return False

        try:
            config = {"configurable": {"thread_id": self._thread_id}}
            checkpoint_tuple = await self._checkpointer.aget_tuple(config)

            if checkpoint_tuple and checkpoint_tuple.checkpoint:
                channel_values = checkpoint_tuple.checkpoint.get("channel_values", {})
                stored_messages = channel_values.get("messages", [])

                if stored_messages:
                    self.messages = []
                    for msg in stored_messages:
                        # Handle different message formats
                        if hasattr(msg, "type") and hasattr(msg, "content"):
                            role = "assistant" if msg.type == "ai" else msg.type
                            if role in ("human", "user"):
                                role = "user"
                            # Skip system messages and tool messages
                            if role in ("user", "assistant"):
                                content = msg.content
                                # Handle content that might be a list
                                if isinstance(content, list):
                                    content = "".join(
                                        block.get("text", "") if isinstance(block, dict) else str(block)
                                        for block in content
                                    )
                                if content:  # Only add non-empty messages
                                    self.messages.append(Message(role=role, content=content))

                    if self.messages:
                        logger.info(f"Restored {len(self.messages)} messages from checkpointer")
                        return True

        except Exception as e:
            logger.warning(f"Failed to restore messages from checkpointer: {e}")

        return False

    async def _init_memory_manager(self) -> None:
        """Initialize long-term memory manager if enabled."""
        from k8sops.config import get_memory_settings

        memory_settings = get_memory_settings()

        if memory_settings.use_long_term:
            from k8sops.memory import MemoryManager

            # Ensure model is created for memory operations
            self._create_model()

            self._memory_manager = MemoryManager(
                session_id=self.session_id,
                settings=memory_settings,
                llm=self._model,
            )
            await self._memory_manager.initialize()
            logger.info("Long-term memory manager initialized")

    async def _get_memory_context(self) -> list[dict]:
        """Retrieve relevant memories for session context."""
        if not self._memory_manager:
            return []

        try:
            memories = await self._memory_manager.retrieve_relevant_memories(
                query="kubernetes troubleshooting cluster operations"
            )
            return memories
        except Exception as e:
            logger.warning(f"Failed to retrieve memories: {e}")
            return []

    async def _check_context_limit(self) -> bool:
        """Check and handle context window limit.

        Returns:
            True if summarization occurred.
        """
        if not self._memory_manager:
            return False

        if self._memory_manager.should_summarize(self.messages):
            self.messages, summary = await self._memory_manager.summarize_and_trim(
                self.messages
            )
            logger.info("Conversation summarized to manage context window")
            return True

        return False

    async def _maybe_extract_memories(self) -> None:
        """Periodically extract and store memories during session.

        Called after each assistant response to ensure memories are stored
        even if session cleanup isn't triggered (e.g., browser tab close).
        """
        if not self._memory_manager:
            return

        try:
            if self._memory_manager.should_extract(self.messages):
                memories = await self._memory_manager.extract_incremental(self.messages)
                if memories:
                    logger.info(f"Stored {len(memories)} memories during session")
        except Exception as e:
            logger.warning(f"Failed to extract memories during session: {e}")

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

        # Check context window limit before processing
        if await self._check_context_limit():
            yield {"type": "system", "content": "Conversation summarized to manage context."}

        # Add user message
        user_message = Message(role="user", content=content.strip())
        self.messages.append(user_message)
        yield {"type": "user_message", "content": user_message.content}

        # Set session title from first user message
        if not self._title_set and self._session_store:
            title = content.strip()[:50]
            if len(content.strip()) > 50:
                title += "..."
            await self._session_store.update_session(self.session_id, title=title)
            self._title_set = True

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

            # Update session metadata (preview and message count)
            if self._session_store:
                await self._session_store.update_session(
                    self.session_id,
                    preview=assistant_content[:100] if assistant_content else "",
                    message_count=len(self.messages),
                )

            # Periodically extract memories during session
            await self._maybe_extract_memories()

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
        # Extract any remaining unextracted memories before cleanup
        if self._memory_manager and self.messages:
            try:
                memories = await self._memory_manager.extract_remaining(self.messages)
                if memories:
                    logger.info(f"Extracted {len(memories)} remaining memories at cleanup")
            except Exception as e:
                logger.error(f"Failed to extract session memories: {e}")

        if self._mcp_client:
            try:
                await self._mcp_client.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting MCP client: {e}")

        if self._session_store:
            try:
                await self._session_store.close()
            except Exception as e:
                logger.error(f"Error closing session store: {e}")

        self._mcp_client = None
        self._agent = None
        self._memory_manager = None
        self._session_store = None
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
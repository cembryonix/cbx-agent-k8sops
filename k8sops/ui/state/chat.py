"""Chat state management for the K8S Ops Agent UI.

This is a thin Reflex wrapper around AgentSession.
"""

import reflex as rx
from typing import TypedDict

from . import session_manager


class Message(TypedDict):
    """A chat message (for Reflex serialization)."""

    role: str  # "user" or "assistant"
    content: str


class ToolCall(TypedDict, total=False):
    """A tool call record (for Reflex serialization)."""

    id: str
    name: str
    arguments: str
    status: str  # "running", "complete", "error"
    output: str
    error: str


class ChatState(rx.State):
    """Reflex state for chat UI - wraps AgentSession."""

    # Messages (synced from AgentSession)
    messages: list[Message] = []
    current_input: str = ""

    # Multi-session support
    _current_session_id: str = ""

    # Streaming state
    is_streaming: bool = False
    is_processing: bool = False

    # Tool calls for current response
    tool_calls: list[ToolCall] = []

    # Available tools (discovered from MCP)
    available_tools: list[dict] = []

    # Connection status
    mcp_connected: bool = False
    agent_ready: bool = False
    error_message: str = ""

    # Current model display
    current_model: str = ""

    def set_input(self, value: str):
        """Update current input."""
        self.current_input = value

    def set_error_message(self, value: str):
        """Set error message."""
        self.error_message = value

    def clear_error(self):
        """Clear error message."""
        self.error_message = ""

    def clear_input(self):
        """Clear input after sending."""
        self.current_input = ""

    def handle_key_down(self, key: str):
        """Handle Enter key to submit."""
        if key == "Enter":
            return self.send_message()

    def _get_session(self):
        """Get AgentSession for current UI session."""
        # Use current_session_id if set, otherwise fall back to browser token
        session_id = getattr(self, '_current_session_id', None)
        if not session_id:
            session_id = self.router.session.client_token
        return session_manager.get_session(session_id)

    def _get_session_id(self) -> str:
        """Get current session ID."""
        session_id = getattr(self, '_current_session_id', None)
        if not session_id:
            session_id = self.router.session.client_token
        return session_id

    def _sync_from_session(self, session):
        """Sync Reflex state from AgentSession."""
        self.messages = [
            {"role": m.role, "content": m.content}
            for m in session.messages
        ]
        self.tool_calls = [
            {
                "id": tc.id,
                "name": tc.name,
                "arguments": tc.arguments,
                "status": tc.status,
                "output": tc.output,
                "error": tc.error,
            }
            for tc in session.tool_calls
        ]
        self.available_tools = session.available_tools
        self.mcp_connected = session.mcp_connected
        self.agent_ready = session.agent_ready
        self.is_streaming = session.is_streaming
        self.is_processing = session.is_processing
        self.error_message = session.error_message
        self.current_model = session.get_current_model()

    async def initialize(self):
        """Initialize MCP client and agent."""
        from k8sops.session import AgentSession

        token = self.router.session.client_token

        # Check if session already exists
        session = session_manager.get_session(token)
        if session and session.agent_ready:
            self._sync_from_session(session)
            return

        # Create new session
        self.is_processing = True
        self.error_message = ""
        yield

        try:
            session = AgentSession(session_id=token)
            await session.initialize()

            # Store session
            session_manager.set_session(token, session)

            # Sync state
            self._sync_from_session(session)

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error_message = f"Failed to initialize: {str(e)}"
            self.mcp_connected = False
            self.agent_ready = False

        finally:
            self.is_processing = False
            yield

    async def send_message(self):
        """Send a message and get agent response."""
        if not self.current_input.strip():
            return

        session = self._get_session()
        if not session or not session.agent_ready:
            self.error_message = "Agent not ready. Please wait for initialization."
            yield
            return

        user_message = self.current_input.strip()
        self.current_input = ""
        self.is_streaming = True
        self.is_processing = True
        self.tool_calls = []

        # Add user message immediately
        self.messages.append({"role": "user", "content": user_message})
        yield

        # Add empty assistant message for streaming
        self.messages.append({"role": "assistant", "content": ""})
        yield

        try:
            async for event in session.send_message(user_message):
                event_type = event.get("type", "")

                if event_type == "token":
                    # Append token to last message
                    self.messages[-1]["content"] += event.get("content", "")
                    yield

                elif event_type == "tool_start":
                    tc = event.get("tool_call")
                    self.tool_calls.append({
                        "id": tc.id,
                        "name": tc.name,
                        "arguments": tc.arguments,
                        "status": tc.status,
                        "output": tc.output,
                        "error": tc.error,
                    })
                    yield

                elif event_type == "tool_end":
                    tc = event.get("tool_call")
                    for i, existing in enumerate(self.tool_calls):
                        if existing["id"] == tc.id:
                            self.tool_calls[i]["status"] = tc.status
                            self.tool_calls[i]["output"] = tc.output
                            break
                    yield

                elif event_type == "error":
                    self.error_message = event.get("message", "Unknown error")
                    yield

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.messages[-1]["content"] = f"Error: {str(e)}"
            self.error_message = str(e)

        finally:
            self.is_streaming = False
            self.is_processing = False
            yield

    async def reinitialize_agent(self):
        """Reinitialize agent with current settings.

        Called when settings change that require agent recreation.
        """
        session = self._get_session()
        if not session:
            return

        self.is_processing = True
        yield

        try:
            # Get settings from SettingsState
            settings_state = await self.get_state(SettingsState)

            # Update session settings
            reinitialized = await session.update_settings(
                provider=settings_state.llm_provider,
                model_name=settings_state.model_name,
                temperature=settings_state.temperature,
            )

            if reinitialized:
                self.current_model = session.get_current_model()
                # Add system message about model change
                self.messages.append({
                    "role": "assistant",
                    "content": f"Model changed to {self.current_model}",
                })

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error_message = f"Failed to reinitialize: {str(e)}"

        finally:
            self.is_processing = False
            yield

    async def cleanup(self):
        """Cleanup resources."""
        token = self.router.session.client_token
        await session_manager.cleanup_session(token)
        self.mcp_connected = False
        self.agent_ready = False

    def clear_chat(self):
        """Clear chat history."""
        session = self._get_session()
        if session:
            session.clear_messages()

        self.messages = []
        self.tool_calls = []
        self.error_message = ""

    async def switch_to_session(self, session_id: str):
        """Switch to a different session.

        Args:
            session_id: ID of session to switch to.
        """
        from k8sops.session import AgentSession

        # Update current session ID
        self._current_session_id = session_id

        # Clear current UI state
        self.messages = []
        self.tool_calls = []
        self.error_message = ""
        self.is_processing = True
        yield

        try:
            # Check if session exists in manager
            session = session_manager.get_session(session_id)

            if session and session.agent_ready:
                # Existing session - sync state
                self._sync_from_session(session)
            else:
                # New or unloaded session - initialize
                session = AgentSession(session_id=session_id)
                await session.initialize()
                session_manager.set_session(session_id, session)
                self._sync_from_session(session)

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error_message = f"Failed to switch session: {str(e)}"
            self.agent_ready = False

        finally:
            self.is_processing = False
            yield

    def save_history(self):
        """Save chat history as downloadable JSON file."""
        import json
        from datetime import datetime

        if not self.messages:
            return

        # Create history data
        history = {
            "session_id": self._get_session_id(),
            "exported_at": datetime.now().isoformat(),
            "messages": self.messages,
            "tool_calls": self.tool_calls,
        }

        # Create JSON content
        content = json.dumps(history, indent=2)

        # Trigger browser download
        filename = f"k8sops-chat-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        return rx.download(data=content, filename=filename)


# Import here to avoid circular import
from .settings import SettingsState

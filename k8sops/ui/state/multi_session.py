"""Multi-session state management for K8S Ops Agent UI.

Manages multiple chat sessions with persistence via Redis.
"""

import uuid
import logging
from datetime import datetime
from typing import TypedDict

import reflex as rx

logger = logging.getLogger(__name__)


def _format_time_ago(iso_time: str) -> str:
    """Format ISO time string as relative time for display."""
    try:
        dt = datetime.fromisoformat(iso_time.replace("Z", "+00:00"))
        now = datetime.now(dt.tzinfo)
        diff = now - dt

        if diff.days == 0:
            if diff.seconds < 60:
                return "Just now"
            elif diff.seconds < 3600:
                minutes = diff.seconds // 60
                return f"{minutes}m ago"
            else:
                hours = diff.seconds // 3600
                return f"{hours}h ago"
        elif diff.days == 1:
            return "Yesterday"
        elif diff.days < 7:
            return f"{diff.days}d ago"
        else:
            return dt.strftime("%b %d")
    except Exception:
        return ""


class SessionInfo(TypedDict):
    """Session info for UI display."""

    session_id: str
    title: str
    preview: str
    message_count: int
    updated_at: str  # ISO format
    time_ago: str  # Formatted relative time for display
    is_current: bool


class MultiSessionState(rx.State):
    """State for managing multiple chat sessions."""

    # List of sessions for sidebar
    sessions: list[SessionInfo] = []

    # Currently active session ID
    current_session_id: str = ""

    # UI state
    show_session_sidebar: bool = True
    is_loading_sessions: bool = False

    # Inline editing state
    editing_session_id: str = ""
    editing_title: str = ""

    # Delete confirmation state
    delete_confirm_session_id: str = ""
    delete_confirm_session_title: str = ""

    # Session store instance (not serialized)
    _session_store_initialized: bool = False

    async def _get_session_store(self):
        """Get or create session store instance based on backend config."""
        from k8sops.config import get_memory_settings
        from k8sops.session import get_session_store

        memory_settings = get_memory_settings()
        return get_session_store(user_id=memory_settings.user_id)

    async def load_sessions(self):
        """Load session list from Redis."""
        logger.info("load_sessions called")
        self.is_loading_sessions = True
        yield

        try:
            store = await self._get_session_store()
            if store is None:
                logger.warning("Session store not available (memory-only mode)")
                self.sessions = []
                return

            logger.info(f"Fetching sessions from store for user: {store.user_id}")
            session_list = await store.list_sessions(limit=10)
            logger.info(f"Got {len(session_list)} sessions from store")
            await store.close()

            self.sessions = [
                {
                    "session_id": s.session_id,
                    "title": s.title,
                    "preview": s.preview,
                    "message_count": s.message_count,
                    "updated_at": s.updated_at,
                    "time_ago": _format_time_ago(s.updated_at),
                    "is_current": s.session_id == self.current_session_id,
                }
                for s in session_list
            ]

            logger.info(f"Loaded {len(self.sessions)} sessions into state")

        except Exception as e:
            logger.error(f"Failed to load sessions: {e}", exc_info=True)
            self.sessions = []

        finally:
            self.is_loading_sessions = False
            yield

    async def new_session(self):
        """Create and switch to a new session."""
        # Generate new session ID
        new_id = str(uuid.uuid4())
        self.current_session_id = new_id

        # The actual session creation happens in ChatState.initialize()
        # when it detects a new session_id

        # Reload session list
        yield MultiSessionState.load_sessions

        # Trigger chat reinitialization
        yield ChatState.switch_to_session(new_id)

    async def switch_session(self, session_id: str):
        """Switch to an existing session.

        Args:
            session_id: ID of session to switch to.
        """
        # Don't switch if currently editing any session
        if self.editing_session_id:
            return

        if session_id == self.current_session_id:
            return

        self.current_session_id = session_id

        # Update is_current flags
        for s in self.sessions:
            s["is_current"] = s["session_id"] == session_id

        yield

        # Trigger chat to load this session
        yield ChatState.switch_to_session(session_id)

    async def delete_session(self, session_id: str):
        """Delete a session.

        Args:
            session_id: ID of session to delete.
        """
        try:
            store = await self._get_session_store()
            if store is None:
                return

            await store.delete_session(session_id)
            await store.close()

            # If deleting current session, switch to newest or create new
            if session_id == self.current_session_id:
                # Remove from local list first
                self.sessions = [s for s in self.sessions if s["session_id"] != session_id]

                if self.sessions:
                    # Switch to most recent session
                    yield MultiSessionState.switch_session(self.sessions[0]["session_id"])
                else:
                    # Create new session
                    yield MultiSessionState.new_session
            else:
                # Just reload the list
                yield MultiSessionState.load_sessions

            logger.info(f"Deleted session {session_id[:8]}...")

        except Exception as e:
            logger.error(f"Failed to delete session: {e}")

    async def rename_session(self, session_id: str, new_title: str):
        """Rename a session.

        Args:
            session_id: ID of session to rename.
            new_title: New title.
        """
        try:
            store = await self._get_session_store()
            if store is None:
                return

            await store.rename_session(session_id, new_title)
            await store.close()

            # Update local list
            for s in self.sessions:
                if s["session_id"] == session_id:
                    s["title"] = new_title
                    break

            yield

        except Exception as e:
            logger.error(f"Failed to rename session: {e}")

    def toggle_sidebar(self):
        """Toggle session sidebar visibility."""
        self.show_session_sidebar = not self.show_session_sidebar

    def set_current_session(self, session_id: str):
        """Set current session ID without triggering switch.

        Used during initial load to set the session ID from URL or storage.
        """
        self.current_session_id = session_id

    # --- Inline rename methods ---

    def start_rename(self, session_id: str):
        """Start inline rename for a session."""
        # Find current title
        for s in self.sessions:
            if s["session_id"] == session_id:
                self.editing_title = s["title"]
                break
        self.editing_session_id = session_id

    def set_editing_title(self, value: str):
        """Update the editing title."""
        self.editing_title = value

    def cancel_rename(self):
        """Cancel inline rename."""
        self.editing_session_id = ""
        self.editing_title = ""

    async def confirm_rename(self):
        """Confirm and save the rename."""
        if self.editing_session_id and self.editing_title.strip():
            yield MultiSessionState.rename_session(
                self.editing_session_id, self.editing_title.strip()
            )
        self.editing_session_id = ""
        self.editing_title = ""

    def handle_rename_key(self, key: str):
        """Handle key press during rename."""
        if key == "Enter":
            return MultiSessionState.confirm_rename
        elif key == "Escape":
            return MultiSessionState.cancel_rename

    # --- Delete confirmation methods ---

    def start_delete(self, session_id: str):
        """Show delete confirmation for a session."""
        # Find session title
        for s in self.sessions:
            if s["session_id"] == session_id:
                self.delete_confirm_session_title = s["title"]
                break
        self.delete_confirm_session_id = session_id

    def cancel_delete(self):
        """Cancel delete confirmation."""
        self.delete_confirm_session_id = ""
        self.delete_confirm_session_title = ""

    async def confirm_delete(self):
        """Confirm and execute delete."""
        if self.delete_confirm_session_id:
            session_id = self.delete_confirm_session_id
            self.delete_confirm_session_id = ""
            self.delete_confirm_session_title = ""
            yield
            yield MultiSessionState.delete_session(session_id)


# Import here to avoid circular import
from .chat import ChatState
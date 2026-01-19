"""Session management module for K8S Ops Agent.

This module provides:
- AgentSession: Core session management class (UI-agnostic)
- SessionSettings: Configuration for agent sessions
- Message: Chat message data class
- ToolCall: Tool call record data class
- SessionStore: Redis-backed session metadata storage
- FileSessionStore: File-based session metadata storage (JSONL)
- SessionMetadata: Session metadata data class
- get_session_store: Factory function to get appropriate store
"""

from k8sops.session.agent_session import (
    AgentSession,
    SessionSettings,
    Message,
    ToolCall,
)
from k8sops.session.store import SessionStore, SessionMetadata
from k8sops.session.file_store import FileSessionStore


def get_session_store(user_id: str = "default"):
    """Factory function to get the appropriate session store based on config.

    Args:
        user_id: User identifier for namespacing sessions.

    Returns:
        SessionStore (Redis), FileSessionStore, or None if memory-only.
    """
    from k8sops.config import get_memory_settings

    settings = get_memory_settings()

    if settings.use_redis:
        return SessionStore(
            redis_url=settings.redis_url,
            user_id=user_id,
        )
    elif settings.use_filesystem:
        return FileSessionStore(
            base_path=settings.get_filesystem_path(),
            user_id=user_id,
        )
    else:
        # Memory-only mode - no persistence
        return None


__all__ = [
    "AgentSession",
    "SessionSettings",
    "Message",
    "ToolCall",
    "SessionStore",
    "FileSessionStore",
    "SessionMetadata",
    "get_session_store",
]
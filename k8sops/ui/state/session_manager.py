"""Session manager for AgentSession instances.

Maps UI session tokens to AgentSession instances.
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from k8sops.session import AgentSession

logger = logging.getLogger(__name__)

# Global storage for sessions (keyed by UI session token)
_sessions: dict[str, "AgentSession"] = {}


def get_session(token: str) -> "AgentSession | None":
    """Get AgentSession for a UI token."""
    return _sessions.get(token)


def set_session(token: str, session: "AgentSession") -> None:
    """Store AgentSession for a UI token."""
    _sessions[token] = session
    logger.info(f"Stored session for token {token[:8]}...")


def has_session(token: str) -> bool:
    """Check if a session exists for token."""
    return token in _sessions


async def cleanup_session(token: str) -> None:
    """Cleanup and remove session for token."""
    session = _sessions.get(token)
    if session:
        await session.cleanup()
        del _sessions[token]
        logger.info(f"Cleaned up session for token {token[:8]}...")


def clear_all_sessions() -> None:
    """Clear all sessions (for shutdown)."""
    _sessions.clear()
    logger.info("Cleared all sessions")


# Legacy compatibility - these delegate to AgentSession
def get_agent(token: str):
    """Get agent for session (legacy compatibility)."""
    session = get_session(token)
    return session._agent if session else None


def get_mcp_client(token: str):
    """Get MCP client for session (legacy compatibility)."""
    session = get_session(token)
    return session._mcp_client if session else None


def get_thread_id(token: str) -> str:
    """Get thread ID for session (legacy compatibility)."""
    session = get_session(token)
    return session._thread_id if session else "default"

"""Session management module for K8S Ops Agent.

This module provides:
- AgentSession: Core session management class (UI-agnostic)
- SessionSettings: Configuration for agent sessions
- Message: Chat message data class
- ToolCall: Tool call record data class
- SessionStore: Redis-backed session metadata storage
- SessionMetadata: Session metadata data class
"""

from k8sops.session.agent_session import (
    AgentSession,
    SessionSettings,
    Message,
    ToolCall,
)
from k8sops.session.store import SessionStore, SessionMetadata

__all__ = [
    "AgentSession",
    "SessionSettings",
    "Message",
    "ToolCall",
    "SessionStore",
    "SessionMetadata",
]
"""Session metadata store for multi-session support.

Manages session metadata in Redis, separate from conversation history
(which is managed by LangGraph checkpointer).
"""

import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any

import redis.asyncio as redis

logger = logging.getLogger(__name__)


@dataclass
class SessionMetadata:
    """Metadata for a chat session."""

    session_id: str
    user_id: str
    title: str
    created_at: str  # ISO format
    updated_at: str  # ISO format
    message_count: int = 0
    preview: str = ""  # Last message preview

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "SessionMetadata":
        """Create from dictionary."""
        return cls(**data)


class SessionStore:
    """Manages session metadata in Redis.

    Storage schema:
    - sessions:{user_id}:index -> Sorted set of session_ids by updated_at
    - sessions:{user_id}:{session_id} -> JSON with session metadata
    - sessions:{user_id}:{session_id}:tool_calls -> List of tool call JSON objects
    """

    def __init__(self, redis_url: str, user_id: str = "default"):
        """Initialize session store.

        Args:
            redis_url: Redis connection URL.
            user_id: User identifier for namespacing sessions.
        """
        self.redis_url = redis_url
        self.user_id = user_id
        self._client: redis.Redis | None = None

    async def _get_client(self) -> redis.Redis:
        """Get or create Redis client."""
        if self._client is None:
            self._client = redis.from_url(self.redis_url)
        return self._client

    def _index_key(self) -> str:
        """Get the sorted set key for session index."""
        return f"sessions:{self.user_id}:index"

    def _session_key(self, session_id: str) -> str:
        """Get the key for session metadata."""
        return f"sessions:{self.user_id}:{session_id}"

    def _tool_calls_key(self, session_id: str) -> str:
        """Get the key for session tool calls."""
        return f"sessions:{self.user_id}:{session_id}:tool_calls"

    async def create_session(
        self,
        session_id: str,
        title: str = "New Chat",
    ) -> SessionMetadata:
        """Create new session metadata.

        Args:
            session_id: Unique session identifier.
            title: Initial session title.

        Returns:
            Created SessionMetadata.
        """
        client = await self._get_client()
        now = datetime.now(timezone.utc).isoformat()

        metadata = SessionMetadata(
            session_id=session_id,
            user_id=self.user_id,
            title=title,
            created_at=now,
            updated_at=now,
            message_count=0,
            preview="",
        )

        # Store metadata as JSON
        await client.set(
            self._session_key(session_id),
            json.dumps(metadata.to_dict()),
        )

        # Add to sorted set index (score = timestamp for ordering)
        timestamp = datetime.now(timezone.utc).timestamp()
        await client.zadd(self._index_key(), {session_id: timestamp})

        logger.info(f"Created session {session_id[:8]}... for user {self.user_id}")
        return metadata

    async def get_session(self, session_id: str) -> SessionMetadata | None:
        """Get session metadata by ID.

        Args:
            session_id: Session identifier.

        Returns:
            SessionMetadata or None if not found.
        """
        client = await self._get_client()
        data = await client.get(self._session_key(session_id))

        if data is None:
            return None

        return SessionMetadata.from_dict(json.loads(data))

    async def list_sessions(self, limit: int = 10) -> list[SessionMetadata]:
        """List sessions ordered by updated_at (most recent first).

        Args:
            limit: Maximum number of sessions to return.

        Returns:
            List of SessionMetadata objects.
        """
        client = await self._get_client()

        # Get session IDs from sorted set (highest score = most recent)
        session_ids = await client.zrevrange(self._index_key(), 0, limit - 1)

        if not session_ids:
            return []

        # Fetch metadata for each session
        sessions = []
        for session_id in session_ids:
            # session_id comes as bytes from Redis
            sid = session_id.decode() if isinstance(session_id, bytes) else session_id
            metadata = await self.get_session(sid)
            if metadata:
                sessions.append(metadata)

        # Sort by updated_at as fallback (ensures consistent ordering)
        sessions.sort(key=lambda s: s.updated_at, reverse=True)

        return sessions

    async def update_session(
        self,
        session_id: str,
        title: str | None = None,
        preview: str | None = None,
        message_count: int | None = None,
    ) -> SessionMetadata | None:
        """Update session metadata.

        Args:
            session_id: Session identifier.
            title: New title (optional).
            preview: New preview text (optional).
            message_count: New message count (optional).

        Returns:
            Updated SessionMetadata or None if not found.
        """
        metadata = await self.get_session(session_id)
        if metadata is None:
            return None

        # Update fields
        if title is not None:
            metadata.title = title
        if preview is not None:
            metadata.preview = preview[:100]  # Truncate preview
        if message_count is not None:
            metadata.message_count = message_count

        # Always update timestamp
        metadata.updated_at = datetime.now(timezone.utc).isoformat()

        # Save updated metadata
        client = await self._get_client()
        await client.set(
            self._session_key(session_id),
            json.dumps(metadata.to_dict()),
        )

        # Update score in sorted set
        timestamp = datetime.now(timezone.utc).timestamp()
        await client.zadd(self._index_key(), {session_id: timestamp})

        logger.debug(f"Updated session {session_id[:8]}...")
        return metadata

    async def delete_session(self, session_id: str) -> bool:
        """Delete session metadata and tool calls.

        Note: This only deletes metadata and tool calls, not checkpoint data.
        Use cleanup_checkpoints() to remove checkpoint data.

        Args:
            session_id: Session identifier.

        Returns:
            True if session was deleted, False if not found.
        """
        client = await self._get_client()

        # Check if exists
        if not await client.exists(self._session_key(session_id)):
            return False

        # Remove from sorted set
        await client.zrem(self._index_key(), session_id)

        # Remove metadata
        await client.delete(self._session_key(session_id))

        # Remove tool calls
        await client.delete(self._tool_calls_key(session_id))

        logger.info(f"Deleted session {session_id[:8]}...")
        return True

    async def rename_session(self, session_id: str, title: str) -> bool:
        """Rename a session.

        Args:
            session_id: Session identifier.
            title: New title.

        Returns:
            True if renamed, False if not found.
        """
        result = await self.update_session(session_id, title=title)
        return result is not None

    async def session_exists(self, session_id: str) -> bool:
        """Check if a session exists.

        Args:
            session_id: Session identifier.

        Returns:
            True if session exists.
        """
        client = await self._get_client()
        return await client.exists(self._session_key(session_id)) > 0

    async def get_session_count(self) -> int:
        """Get total number of sessions for user.

        Returns:
            Number of sessions.
        """
        client = await self._get_client()
        return await client.zcard(self._index_key())

    async def enforce_session_limit(self, max_sessions: int = 10) -> list[str]:
        """Delete oldest sessions if over limit.

        Args:
            max_sessions: Maximum number of sessions to keep.

        Returns:
            List of deleted session IDs.
        """
        client = await self._get_client()
        count = await self.get_session_count()

        if count <= max_sessions:
            return []

        # Get oldest sessions (lowest scores)
        to_delete_count = count - max_sessions
        oldest_ids = await client.zrange(self._index_key(), 0, to_delete_count - 1)

        deleted = []
        for session_id in oldest_ids:
            sid = session_id.decode() if isinstance(session_id, bytes) else session_id
            if await self.delete_session(sid):
                deleted.append(sid)

        if deleted:
            logger.info(f"Enforced session limit: deleted {len(deleted)} oldest sessions")

        return deleted

    async def delete_all_sessions(self) -> int:
        """Delete all sessions for user.

        Returns:
            Number of sessions deleted.
        """
        sessions = await self.list_sessions(limit=100)
        count = 0

        for session in sessions:
            if await self.delete_session(session.session_id):
                count += 1

        logger.info(f"Deleted all {count} sessions for user {self.user_id}")
        return count

    async def append_tool_call(
        self,
        session_id: str,
        tool_call: dict,
    ) -> None:
        """Append a tool call to session.

        Args:
            session_id: Session identifier.
            tool_call: Tool call dict with id, name, arguments, status, output, error.
        """
        client = await self._get_client()
        tool_call_data = {
            "id": tool_call.get("id", ""),
            "name": tool_call.get("name", ""),
            "arguments": tool_call.get("arguments", ""),
            "status": tool_call.get("status", "complete"),
            "output": tool_call.get("output", ""),
            "error": tool_call.get("error", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await client.rpush(self._tool_calls_key(session_id), json.dumps(tool_call_data))
        logger.debug(f"Appended tool call {tool_call.get('name')} to session {session_id[:8]}...")

    async def get_tool_calls(self, session_id: str) -> list[dict]:
        """Get all tool calls for a session.

        Args:
            session_id: Session identifier.

        Returns:
            List of tool call dicts.
        """
        client = await self._get_client()
        tool_calls_data = await client.lrange(self._tool_calls_key(session_id), 0, -1)

        tool_calls = []
        for data in tool_calls_data:
            try:
                tc_str = data.decode() if isinstance(data, bytes) else data
                tc = json.loads(tc_str)
                tool_calls.append({
                    "id": tc.get("id", ""),
                    "name": tc.get("name", ""),
                    "arguments": tc.get("arguments", ""),
                    "status": tc.get("status", "complete"),
                    "output": tc.get("output", ""),
                    "error": tc.get("error", ""),
                })
            except (json.JSONDecodeError, AttributeError):
                continue

        return tool_calls

    async def close(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None
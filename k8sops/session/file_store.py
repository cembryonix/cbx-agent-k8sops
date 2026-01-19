"""File-based session store using JSONL files.

Follows Claude Code's storage pattern:
- sessions.jsonl: Index file for quick listing
- sessions/<user_id>/<session_id>.jsonl: Full conversation data
"""

import json
import logging
import os
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from k8sops.session.store import SessionMetadata

logger = logging.getLogger(__name__)


class FileSessionStore:
    """Manages session metadata using local JSONL files.

    Storage structure:
    ~/.k8sops/
    ├── sessions.jsonl                 # Index file (all sessions, sorted by updated_at)
    └── sessions/
        └── <user_id>/
            └── <session_id>.jsonl     # Session conversation + metadata
    """

    def __init__(self, base_path: str = "~/.k8sops", user_id: str = "default"):
        """Initialize file session store.

        Args:
            base_path: Base directory for storage (default: ~/.k8sops)
            user_id: User identifier for namespacing sessions.
        """
        self.base_path = Path(os.path.expanduser(base_path))
        self.user_id = user_id
        self.index_file = self.base_path / "sessions.jsonl"
        self.sessions_dir = self.base_path / "sessions" / user_id

        # Ensure directories exist
        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        """Ensure storage directories exist."""
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def _session_file(self, session_id: str) -> Path:
        """Get path to session file."""
        return self.sessions_dir / f"{session_id}.jsonl"

    def _read_index(self) -> list[dict]:
        """Read all entries from index file."""
        if not self.index_file.exists():
            return []

        entries = []
        try:
            with open(self.index_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entry = json.loads(line)
                            # Filter by user_id
                            if entry.get("user_id") == self.user_id:
                                entries.append(entry)
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.error(f"Error reading index file: {e}")

        return entries

    def _write_index(self, entries: list[dict]) -> None:
        """Write all entries to index file (rewrite entire file)."""
        try:
            # Read all entries (including other users)
            all_entries = []
            if self.index_file.exists():
                with open(self.index_file, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                entry = json.loads(line)
                                # Keep entries from other users
                                if entry.get("user_id") != self.user_id:
                                    all_entries.append(entry)
                            except json.JSONDecodeError:
                                continue

            # Add current user's entries
            all_entries.extend(entries)

            # Write all entries
            with open(self.index_file, "w") as f:
                for entry in all_entries:
                    f.write(json.dumps(entry) + "\n")

        except Exception as e:
            logger.error(f"Error writing index file: {e}")

    def _append_to_session(self, session_id: str, event: dict) -> None:
        """Append an event to session file."""
        session_file = self._session_file(session_id)
        try:
            with open(session_file, "a") as f:
                f.write(json.dumps(event) + "\n")
        except Exception as e:
            logger.error(f"Error appending to session file: {e}")

    def _read_session_metadata(self, session_id: str) -> dict | None:
        """Read metadata from session file (first line with type=metadata)."""
        session_file = self._session_file(session_id)
        if not session_file.exists():
            return None

        try:
            with open(session_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            event = json.loads(line)
                            if event.get("type") == "metadata":
                                return event
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.error(f"Error reading session file: {e}")

        return None

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

        # Write metadata to session file
        event = {"type": "metadata", **metadata.to_dict()}
        self._append_to_session(session_id, event)

        # Update index
        entries = self._read_index()
        entries.append(metadata.to_dict())
        self._write_index(entries)

        logger.info(f"Created session {session_id[:8]}... for user {self.user_id}")
        return metadata

    async def get_session(self, session_id: str) -> SessionMetadata | None:
        """Get session metadata by ID.

        Args:
            session_id: Session identifier.

        Returns:
            SessionMetadata or None if not found.
        """
        # Try to get from index first (faster)
        entries = self._read_index()
        for entry in entries:
            if entry.get("session_id") == session_id:
                return SessionMetadata.from_dict(entry)

        return None

    async def list_sessions(self, limit: int = 10) -> list[SessionMetadata]:
        """List sessions ordered by updated_at (most recent first).

        Args:
            limit: Maximum number of sessions to return.

        Returns:
            List of SessionMetadata objects.
        """
        entries = self._read_index()

        # Sort by updated_at descending
        entries.sort(key=lambda x: x.get("updated_at", ""), reverse=True)

        # Limit results
        entries = entries[:limit]

        return [SessionMetadata.from_dict(e) for e in entries]

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
        entries = self._read_index()

        for i, entry in enumerate(entries):
            if entry.get("session_id") == session_id:
                # Update fields
                if title is not None:
                    entry["title"] = title
                if preview is not None:
                    entry["preview"] = preview[:100]
                if message_count is not None:
                    entry["message_count"] = message_count

                # Always update timestamp
                entry["updated_at"] = datetime.now(timezone.utc).isoformat()

                entries[i] = entry
                self._write_index(entries)

                # Also update the session file metadata
                self._update_session_file_metadata(session_id, entry)

                logger.debug(f"Updated session {session_id[:8]}...")
                return SessionMetadata.from_dict(entry)

        return None

    def _update_session_file_metadata(self, session_id: str, metadata: dict) -> None:
        """Update metadata in session file (rewrite first line)."""
        session_file = self._session_file(session_id)
        if not session_file.exists():
            return

        try:
            # Read all lines
            with open(session_file, "r") as f:
                lines = f.readlines()

            # Find and update metadata line
            updated = False
            for i, line in enumerate(lines):
                try:
                    event = json.loads(line.strip())
                    if event.get("type") == "metadata":
                        event.update(metadata)
                        event["type"] = "metadata"
                        lines[i] = json.dumps(event) + "\n"
                        updated = True
                        break
                except json.JSONDecodeError:
                    continue

            # If no metadata line found, prepend one
            if not updated:
                metadata["type"] = "metadata"
                lines.insert(0, json.dumps(metadata) + "\n")

            # Write back
            with open(session_file, "w") as f:
                f.writelines(lines)

        except Exception as e:
            logger.error(f"Error updating session file metadata: {e}")

    async def delete_session(self, session_id: str) -> bool:
        """Delete session metadata and file.

        Args:
            session_id: Session identifier.

        Returns:
            True if session was deleted, False if not found.
        """
        # Remove from index
        entries = self._read_index()
        original_len = len(entries)
        entries = [e for e in entries if e.get("session_id") != session_id]

        if len(entries) == original_len:
            return False

        self._write_index(entries)

        # Delete session file
        session_file = self._session_file(session_id)
        if session_file.exists():
            session_file.unlink()

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
        session_file = self._session_file(session_id)
        return session_file.exists()

    async def get_session_count(self) -> int:
        """Get total number of sessions for user.

        Returns:
            Number of sessions.
        """
        entries = self._read_index()
        return len(entries)

    async def enforce_session_limit(self, max_sessions: int = 10) -> list[str]:
        """Delete oldest sessions if over limit.

        Args:
            max_sessions: Maximum number of sessions to keep.

        Returns:
            List of deleted session IDs.
        """
        entries = self._read_index()

        if len(entries) <= max_sessions:
            return []

        # Sort by updated_at ascending (oldest first)
        entries.sort(key=lambda x: x.get("updated_at", ""))

        # Get sessions to delete
        to_delete_count = len(entries) - max_sessions
        to_delete = entries[:to_delete_count]

        deleted = []
        for entry in to_delete:
            session_id = entry.get("session_id")
            if session_id and await self.delete_session(session_id):
                deleted.append(session_id)

        if deleted:
            logger.info(f"Enforced session limit: deleted {len(deleted)} oldest sessions")

        return deleted

    async def delete_all_sessions(self) -> int:
        """Delete all sessions for user.

        Returns:
            Number of sessions deleted.
        """
        entries = self._read_index()
        count = 0

        for entry in entries:
            session_id = entry.get("session_id")
            if session_id and await self.delete_session(session_id):
                count += 1

        logger.info(f"Deleted all {count} sessions for user {self.user_id}")
        return count

    async def append_message(
        self,
        session_id: str,
        role: str,
        content: str,
    ) -> None:
        """Append a message to session file.

        Args:
            session_id: Session identifier.
            role: Message role (user/assistant).
            content: Message content.
        """
        event = {
            "type": "message",
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._append_to_session(session_id, event)

    async def append_tool_call(
        self,
        session_id: str,
        tool_call: dict,
    ) -> None:
        """Append a tool call to session file.

        Args:
            session_id: Session identifier.
            tool_call: Tool call dict with id, name, arguments, status, output, error.
        """
        event = {
            "type": "tool_call",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **tool_call,
        }
        self._append_to_session(session_id, event)

    async def get_messages(self, session_id: str) -> list[dict]:
        """Get all messages from session file.

        Args:
            session_id: Session identifier.

        Returns:
            List of message dicts with role and content.
        """
        session_file = self._session_file(session_id)
        if not session_file.exists():
            return []

        messages = []
        try:
            with open(session_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            event = json.loads(line)
                            if event.get("type") == "message":
                                messages.append({
                                    "role": event.get("role"),
                                    "content": event.get("content"),
                                })
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.error(f"Error reading session messages: {e}")

        return messages

    async def get_tool_calls(self, session_id: str) -> list[dict]:
        """Get all tool calls from session file.

        Args:
            session_id: Session identifier.

        Returns:
            List of tool call dicts.
        """
        session_file = self._session_file(session_id)
        if not session_file.exists():
            return []

        tool_calls = []
        try:
            with open(session_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            event = json.loads(line)
                            if event.get("type") == "tool_call":
                                tool_calls.append({
                                    "id": event.get("id", ""),
                                    "name": event.get("name", ""),
                                    "arguments": event.get("arguments", ""),
                                    "status": event.get("status", "complete"),
                                    "output": event.get("output", ""),
                                    "error": event.get("error", ""),
                                })
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.error(f"Error reading session tool calls: {e}")

        return tool_calls

    async def close(self) -> None:
        """Close the store (no-op for file store, but matches Redis API)."""
        pass
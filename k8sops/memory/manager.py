"""Long-term memory manager for K8sOps agent."""

import json
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel

from k8sops.config import MemorySettings
from k8sops.models import create_embeddings
from .prompts import SUMMARIZATION_PROMPT, MEMORY_EXTRACTION_PROMPT

logger = logging.getLogger(__name__)


class MemoryManager:
    """Manages long-term memory for an agent session.

    Handles:
    - Context window management (summarization when approaching limit)
    - Session end memory extraction
    - Memory retrieval for new sessions
    """

    def __init__(
        self,
        session_id: str,
        settings: MemorySettings,
        llm: BaseChatModel,
    ):
        """Initialize memory manager.

        Args:
            session_id: Current session identifier.
            settings: Memory configuration settings.
            llm: Language model for summarization and extraction.
        """
        self.session_id = session_id
        self.settings = settings
        self.llm = llm
        self.user_id = settings.user_id
        self.namespace = (self.user_id, "k8sops")

        self._store: Any = None
        self._embeddings: Embeddings | None = None
        self._initialized = False

        # Track extraction progress to avoid re-extracting same messages
        self._last_extracted_index = 0
        self._extraction_interval = 5  # Extract every N messages

    async def initialize(self) -> None:
        """Initialize the long-term memory store with embeddings."""
        if self._initialized:
            return

        if not self.settings.use_long_term:
            logger.info("Long-term memory disabled")
            return

        from langgraph.store.redis import AsyncRedisStore

        # Create embeddings
        self._embeddings = create_embeddings(
            provider=self.settings.embedding_provider,
            model=self.settings.get_embedding_model(),
        )

        # Create async embedding function for RedisStore
        async def embed_func(texts: list[str]) -> list[list[float]]:
            return await self._embeddings.aembed_documents(texts)

        # Initialize RedisStore with vector search
        self._store = AsyncRedisStore(
            redis_url=self.settings.redis_url,
            index={
                "embed": embed_func,
                "dims": self.settings.get_embedding_dims(),
                "fields": ["content"],
            },
        )
        await self._store.setup()

        self._initialized = True
        logger.info(
            f"Long-term memory initialized for user '{self.user_id}' "
            f"with {self.settings.embedding_provider} embeddings"
        )

    def count_tokens(self, messages: list[Any]) -> int:
        """Approximate token count for messages.

        Uses a simple heuristic: ~4 characters per token.
        For more accuracy, use tiktoken with specific model.

        Args:
            messages: List of Message objects.

        Returns:
            Estimated token count.
        """
        total_chars = sum(len(m.content) for m in messages)
        return total_chars // 4

    def should_summarize(self, messages: list[Any]) -> bool:
        """Check if we should summarize to manage context window.

        Args:
            messages: Current conversation messages.

        Returns:
            True if token count exceeds threshold.
        """
        if not self._initialized:
            return False

        token_count = self.count_tokens(messages)
        threshold = int(self.settings.max_context_tokens * self.settings.context_threshold)

        if token_count > threshold:
            logger.info(
                f"Token count {token_count} exceeds threshold {threshold}, "
                "summarization recommended"
            )
            return True

        return False

    async def summarize_and_trim(
        self,
        messages: list[Any],
        keep_recent: int = 4,
    ) -> tuple[list[Any], str]:
        """Summarize older messages and return trimmed list.

        Args:
            messages: Full message list.
            keep_recent: Number of recent messages to keep unsummarized.

        Returns:
            Tuple of (trimmed messages with summary, summary text).
        """
        if len(messages) <= keep_recent:
            return messages, ""

        # Split messages
        to_summarize = messages[:-keep_recent]
        to_keep = messages[-keep_recent:]

        # Format messages for summarization
        formatted = "\n".join(
            f"{m.role.upper()}: {m.content}" for m in to_summarize
        )

        # Generate summary
        prompt = SUMMARIZATION_PROMPT.format(messages=formatted)
        response = await self.llm.ainvoke(prompt)
        summary = response.content if hasattr(response, "content") else str(response)

        # Store summary as episodic memory
        await self.store_memory(
            memory_type="episodic",
            content={
                "type": "conversation_summary",
                "summary": summary,
                "message_count": len(to_summarize),
                "source_session": self.session_id,
            },
            tags=["summary", "context_management"],
        )

        # Create summary message to prepend
        from k8sops.session import Message
        summary_message = Message(
            role="assistant",
            content=f"[Previous conversation summary: {summary}]",
        )

        logger.info(f"Summarized {len(to_summarize)} messages, keeping {len(to_keep)}")

        return [summary_message] + to_keep, summary

    async def extract_session_memories(self, messages: list[Any]) -> list[dict]:
        """Extract and store key memories from all session messages.

        Note: Prefer extract_remaining() for cleanup which only processes
        messages that haven't been extracted yet.

        Args:
            messages: All session messages.

        Returns:
            List of extracted memories.
        """
        if not self._initialized or not messages:
            return []

        return await self._extract_memories_from_messages(messages)

    def should_extract(self, messages: list[Any]) -> bool:
        """Check if we should extract memories from new messages.

        Triggers extraction every N messages after the last extraction point.

        Args:
            messages: Current conversation messages.

        Returns:
            True if extraction should run.
        """
        if not self._initialized:
            return False

        new_messages = len(messages) - self._last_extracted_index
        return new_messages >= self._extraction_interval

    async def extract_incremental(self, messages: list[Any]) -> list[dict]:
        """Extract memories from new messages since last extraction.

        Called periodically during session to ensure memories are stored
        even if cleanup isn't called (e.g., browser close).

        Args:
            messages: All session messages.

        Returns:
            List of extracted memories.
        """
        if not self._initialized:
            return []

        # Only process messages since last extraction
        new_messages = messages[self._last_extracted_index:]
        if not new_messages:
            return []

        # Skip if not enough new messages (unless forced at cleanup)
        if len(new_messages) < self._extraction_interval:
            return []

        logger.info(
            f"Incremental extraction: processing {len(new_messages)} new messages "
            f"(index {self._last_extracted_index} to {len(messages)})"
        )

        # Extract from new messages only
        memories = await self._extract_memories_from_messages(new_messages)

        # Update tracking
        self._last_extracted_index = len(messages)

        return memories

    async def extract_remaining(self, messages: list[Any]) -> list[dict]:
        """Extract memories from any remaining unprocessed messages.

        Called at cleanup to ensure no messages are missed.
        Unlike extract_incremental, this ignores the interval threshold.

        Args:
            messages: All session messages.

        Returns:
            List of extracted memories.
        """
        if not self._initialized:
            return []

        # Only process messages since last extraction
        new_messages = messages[self._last_extracted_index:]
        if not new_messages:
            logger.debug("No remaining messages to extract at cleanup")
            return []

        logger.info(
            f"Cleanup extraction: processing {len(new_messages)} remaining messages "
            f"(index {self._last_extracted_index} to {len(messages)})"
        )

        # Extract from remaining messages
        memories = await self._extract_memories_from_messages(new_messages)

        # Update tracking
        self._last_extracted_index = len(messages)

        return memories

    async def _extract_memories_from_messages(self, messages: list[Any]) -> list[dict]:
        """Internal method to extract and store memories from a message list.

        Args:
            messages: Messages to extract from.

        Returns:
            List of extracted memories.
        """
        if not messages:
            return []

        # Format messages
        formatted = "\n".join(
            f"{m.role.upper()}: {m.content}" for m in messages
        )

        # Extract memories using LLM
        prompt = MEMORY_EXTRACTION_PROMPT.format(messages=formatted)
        response = await self.llm.ainvoke(prompt)
        response_text = response.content if hasattr(response, "content") else str(response)

        # Parse JSON response
        try:
            json_start = response_text.find("[")
            json_end = response_text.rfind("]") + 1
            if json_start >= 0 and json_end > json_start:
                memories = json.loads(response_text[json_start:json_end])
            else:
                logger.warning("No JSON array found in memory extraction response")
                memories = []
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse memory extraction response: {e}")
            memories = []

        # Store each memory
        stored = []
        for memory in memories:
            if isinstance(memory, dict) and "content" in memory:
                await self.store_memory(
                    memory_type=memory.get("type", "semantic"),
                    content={"content": memory["content"]},
                    tags=memory.get("tags", []),
                )
                stored.append(memory)

        if stored:
            logger.info(f"Extracted and stored {len(stored)} memories")

        return stored

    async def store_memory(
        self,
        memory_type: str,
        content: dict,
        tags: list[str] | None = None,
    ) -> str:
        """Store a memory to long-term storage.

        Args:
            memory_type: "semantic" or "episodic".
            content: Memory content dict.
            tags: Optional tags for filtering.

        Returns:
            Memory key.
        """
        if not self._initialized:
            return ""

        key = f"{memory_type}_{uuid4().hex[:8]}"
        value = {
            **content,
            "type": memory_type,
            "tags": tags or [],
            "source_session": self.session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        await self._store.aput(self.namespace, key, value)
        logger.debug(f"Stored memory: {key}")

        return key

    async def retrieve_relevant_memories(
        self,
        query: str,
        memory_type: str | None = None,
    ) -> list[dict]:
        """Retrieve relevant memories for a query.

        Args:
            query: Search query for semantic matching.
            memory_type: Optional filter by type ("semantic" or "episodic").

        Returns:
            List of relevant memory dicts.
        """
        if not self._initialized:
            return []

        filter_dict = {"type": memory_type} if memory_type else None

        try:
            items = await self._store.asearch(
                self.namespace,
                query=query,
                filter=filter_dict,
                limit=self.settings.max_memories,
            )

            memories = [item.value for item in items]
            logger.debug(f"Retrieved {len(memories)} memories for query: {query[:50]}...")
            return memories

        except Exception as e:
            logger.error(f"Failed to retrieve memories: {e}")
            return []

    def format_memories_for_context(self, memories: list[dict]) -> str:
        """Format memories for inclusion in agent context.

        Args:
            memories: List of memory dicts.

        Returns:
            Formatted string for context injection.
        """
        if not memories:
            return ""

        lines = []
        for mem in memories:
            mem_type = mem.get("type", "unknown")
            content = mem.get("content", mem.get("summary", ""))
            if content:
                lines.append(f"- [{mem_type}] {content}")

        return "\n".join(lines)
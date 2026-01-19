"""Prompts for memory operations."""

SUMMARIZATION_PROMPT = """Summarize the following conversation between a user and a Kubernetes operations assistant.

Preserve the following information:
- Key decisions made
- Important facts discovered about the cluster/environment
- Actions taken and their outcomes (commands run, results)
- Any unresolved issues or pending tasks

Be concise but comprehensive. Focus on information that would be useful for continuing the conversation.

Conversation:
{messages}

Summary:"""

MEMORY_EXTRACTION_PROMPT = """Analyze this K8sOps troubleshooting session and extract key learnings for future reference.

Extract the following types of information as a JSON array:

1. **Semantic memories** (facts about the user's environment):
   - Cluster names, regions, providers
   - Namespace preferences
   - Common resource patterns
   - User preferences for tools/approaches

2. **Episodic memories** (session summaries):
   - Problem encountered and symptoms
   - Root cause identified
   - Solution applied
   - Tools/commands that were useful

Return a JSON array of memory objects. Each object should have:
- "type": "semantic" or "episodic"
- "content": The fact or summary (string)
- "tags": Relevant tags for search (array of strings)

Session:
{messages}

JSON array of memories:"""

MEMORY_CONTEXT_PROMPT = """Based on these relevant memories from previous sessions, here is context that may help:

{memories}

Use this context to provide more informed assistance, but don't explicitly mention that you're using past memories unless relevant."""
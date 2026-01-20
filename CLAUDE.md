# K8SOps Agent - Instructions for AI Assistants

## Project Overview

K8SOps is a Kubernetes operations AI assistant with Reflex UI, LangGraph agent, and MCP client. It features multi-session support, long-term memory, and streaming responses.

## Tech Stack

- **UI**: Reflex (Python web framework, compiles to React)
- **Agent**: LangGraph ReAct agent with streaming
- **LLM**: Anthropic, OpenAI, or Ollama (configurable)
- **Tools**: MCP (Model Context Protocol) for kubectl/helm/argocd
- **Memory**: Long-term memory with semantic search (Redis/filesystem backend)
- **Sessions**: Multi-session support with Redis-backed session store
- **Config**: Pydantic settings + YAML defaults

## Key Files

| File | Purpose |
|------|---------|
| `k8sops/session/` | Session management submodule |
| `k8sops/session/agent_session.py` | Core AgentSession - UI-agnostic session logic |
| `k8sops/session/store.py` | SessionStore - Redis-backed session metadata |
| `k8sops/session/file_store.py` | File storage for session artifacts |
| `k8sops/ui/state/chat.py` | ChatState - Reflex UI state |
| `k8sops/ui/state/settings.py` | SettingsState - model/provider selection |
| `k8sops/ui/state/multi_session.py` | Multi-session state management |
| `k8sops/agent/factory.py` | LangGraph agent creation |
| `k8sops/agent/prompts.py` | System prompts and agent instructions |
| `k8sops/mcp_client/client.py` | MCP server connection |
| `k8sops/models/factory.py` | LLM provider abstraction |
| `k8sops/memory/manager.py` | Long-term memory manager with semantic search |
| `k8sops/config/defaults/models.yaml` | Provider/model catalog |
| `k8sops/config/defaults/settings.yaml` | Default configuration values |

## Common Tasks

### Add a new LLM model
Edit `k8sops/config/defaults/models.yaml` - no Python changes needed.

### Add UI component
Create in `k8sops/ui/components/`, import in relevant page.

### Modify agent behavior
Edit `k8sops/agent/prompts.py` for system prompt changes.

### Change default settings
Edit `k8sops/config/defaults/settings.yaml` or set environment variables.

### Enable long-term memory
Set `MEMORY_LONG_TERM_ENABLED=true` and configure `MEMORY_BACKEND` (redis/filesystem/memory) and `EMBEDDING_PROVIDER` (openai/ollama).

## Running

```bash
# Start app
reflex run

# Run tests
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/e2e/ -v
python tests/validation/run_validation.py
```

## Architecture Rules

1. **AgentSession is UI-agnostic** - Don't add Reflex imports to `k8sops/session/`
2. **UI is thin wrapper** - Business logic belongs in AgentSession, not ChatState
3. **Config from YAML** - Avoid hardcoding model names in Python
4. **Checkpointer preserved** - Model switches must not reset conversation history
5. **Memory is optional** - Long-term memory is opt-in via `MEMORY_LONG_TERM_ENABLED`
6. **Sessions are independent** - Each session has its own agent, checkpointer, and memory context

## Key Features

### Long-term Memory
- Semantic search across previous sessions
- Automatic memory extraction from conversations
- Context window management with summarization
- Supports Redis, filesystem, or in-memory backends

### Multi-session Support
- Multiple concurrent chat sessions
- Session metadata stored in Redis
- Each session maintains independent conversation state

## Code Style

Follow [PEP 8](https://peps.python.org/pep-0008/) with these key points:

### Imports
- All imports at the top of the file, after module docstring
- Group in order: standard library → third-party → local application
- One import per line; avoid wildcard imports (`from x import *`)

### Formatting
- 4 spaces for indentation (no tabs)
- Max line length: 100 characters (Ruff default, per `pyproject.toml`)
- Two blank lines between top-level definitions; one between methods
- No trailing whitespace

### Naming
- Functions/variables: `lowercase_with_underscores`
- Classes: `CapWords`
- Constants: `UPPER_CASE_WITH_UNDERSCORES`
- No leading underscores for module-level variables (project rule)

### Whitespace
- No extra spaces inside parentheses, brackets, braces
- Surround binary operators with single spaces
- No spaces around `=` in keyword arguments

### Other
- Use type hints
- Async/await for all I/O operations
- Use `is`/`is not` for None comparisons
- Prefer `isinstance()` over direct type comparisons
- Icons use Lucide names (e.g., `circle-check`, not `check-circle`)

## Dependencies

All in `requirements.txt`. Key packages:
- `reflex` - UI framework
- `langgraph`, `langchain-core` - Agent framework
- `langgraph-checkpoint-redis`, `redis` - Session persistence
- `mcp`, `langchain-mcp-adapters` - Tool integration
- `pydantic-settings` - Configuration
- `langchain-openai`, `langchain-anthropic`, `langchain-ollama` - LLM providers

## Environment Variables

### Required
- `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` or `OLLAMA_BASE_URL` - LLM provider API key/URL
- `MCP_SERVER_URL` - MCP server endpoint
- `MCP_TRANSPORT` - `http` or `stdio`

### Optional
- `REDIS_URL` - Redis connection URL (for checkpointer and session store)
- `MEMORY_LONG_TERM_ENABLED` - Enable long-term memory (default: `false`)
- `MEMORY_BACKEND` - Memory backend: `redis`, `filesystem`, or `memory` (default: `memory`)
- `EMBEDDING_PROVIDER` - Embedding provider for memory: `openai` or `ollama` (default: `openai`)
- `EMBEDDING_MODEL` - Embedding model name (auto-detected if not specified)
- `LLM_PROVIDER` - Default LLM provider: `anthropic`, `openai`, or `ollama`
- `LLM_MODEL` - Default model name (overrides `models.yaml` default)
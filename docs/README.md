# K8SOps Agent

A Python-based AI assistant for managing Kubernetes clusters. K8SOps provides a chat interface where users interact with an AI agent that uses MCP (Model Context Protocol) tools to execute kubectl, helm, and argocd commands.

## Architecture

K8SOps follows a four-layer architecture:

```
┌─────────────────────────────────────────────────────────────┐
│  UI Layer (Reflex)                                          │
│  - Chat interface with real-time streaming                  │
│  - Settings panel (provider, model, temperature)            │
│  - Thin wrapper around AgentSession                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  AgentSession (Core - UI Agnostic)                          │
│  - Session settings (provider, model, temp)                 │
│  - Conversation history (preserved across model switches)   │
│  - Can be used by UI, CLI, or tests                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Agent Layer (LangGraph)                                    │
│  - ReAct agent with create_react_agent()                    │
│  - Real-time streaming via astream_events()                 │
│  - Checkpointer (MemorySaver or RedisSaver)                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  MCP Client Layer                                           │
│  - Single server connection                                 │
│  - Dynamic tool discovery via tools/list                    │
│  - HTTP or stdio transport                                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  MCP-K8S Server (external)                                  │
│  - kubectl, helm, argocd tools                              │
└─────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
k8sops/
├── __init__.py             # Exports AgentSession, SessionSettings
├── k8sops.py               # Reflex entry point
│
├── session/                # Session Management Module
│   ├── __init__.py         # Exports and factory function
│   ├── agent_session.py    # AgentSession - core session management
│   ├── store.py            # SessionStore - Redis session metadata
│   └── file_store.py       # FileSessionStore - JSONL file storage
│
├── ui/                     # UI Layer (Reflex)
│   ├── app.py              # rx.App definition
│   ├── styles.py           # Global styles
│   ├── state/
│   │   ├── base.py         # BaseState (sidebar toggle)
│   │   ├── chat.py         # ChatState (wraps AgentSession)
│   │   ├── settings.py     # SettingsState (triggers agent reinit)
│   │   ├── multi_session.py # Multi-session sidebar state
│   │   └── session_manager.py  # Maps UI tokens to AgentSession
│   ├── components/
│   │   ├── chat/           # Message bubbles, input bar
│   │   ├── sidebar/        # Settings panel, session list
│   │   ├── tool_panel/     # Tool call visualization
│   │   └── common/         # Markdown, code blocks
│   └── pages/
│       └── index.py        # Main page layout
│
├── agent/                  # Agent Layer (LangGraph)
│   ├── factory.py          # create_agent(), create_agent_with_mcp()
│   └── prompts.py          # System prompts
│
├── mcp_client/             # MCP Client Layer
│   └── client.py           # MCPClient class
│
├── models/                 # LLM Providers
│   └── factory.py          # create_model() - Anthropic/OpenAI/Ollama
│
└── config/                 # Configuration
    ├── __init__.py         # Exports settings and loader functions
    ├── settings.py         # Pydantic settings (from .env)
    ├── loader.py           # YAML config loader
    └── defaults/           # Built-in defaults (YAML)
        ├── models.yaml     # Provider/model definitions
        └── settings.yaml   # App default settings
```

## Core Components

### AgentSession

The heart of the system - UI-agnostic session management.

```python
from k8sops import AgentSession, SessionSettings

session = AgentSession(session_id="my-session")
await session.initialize()

async for event in session.send_message("List all pods"):
    if event["type"] == "token":
        print(event["content"], end="")
    elif event["type"] == "tool_start":
        print(f"\nUsing tool: {event['name']}")
```

Key features:
- Conversation history preserved across model switches
- Streaming responses with fine-grained events
- Status tracking (mcp_connected, agent_ready, is_processing)

### MCP Client

Connects to a single MCP server with dynamic tool discovery.

Supported transports:
- **HTTP**: Remote server connection
- **stdio**: Local process spawning

Tools are discovered at runtime - no hardcoding required.

### Model Factory

Supports multiple LLM providers:
- **Anthropic**: Claude models (requires `ANTHROPIC_API_KEY`)
- **OpenAI**: GPT models (requires `OPENAI_API_KEY`)
- **Ollama**: Local models (requires `OLLAMA_BASE_URL`)

### Configuration

Two-layer configuration system:

1. **YAML defaults** (`config/defaults/`): Provider/model catalog, app settings
2. **Environment variables**: Override defaults, API keys

To add a new model, edit `config/defaults/models.yaml`:

```yaml
providers:
  anthropic:
    name: "Anthropic"
    default_model: "claude-sonnet-4-5-20250929"
    models:
      - id: "claude-sonnet-4-5-20250929"
        name: "Claude Sonnet 4.5"
      - id: "claude-opus-4-5-20251101"
        name: "Claude Opus 4.5"
```

Helper functions:
```python
from k8sops.config import get_providers, get_model_ids_for_provider, get_default_model

get_providers()                        # ['anthropic', 'openai', 'ollama']
get_model_ids_for_provider('anthropic')  # ['claude-sonnet-4-5-20250929', ...]
get_default_model('anthropic')           # 'claude-sonnet-4-5-20250929'
```

## Running the Application

### Prerequisites

- Python 3.11+
- MCP-K8S Server running (external service)
- API key for chosen provider (or Ollama running locally)

### Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings
```

### Environment Variables

```bash
# LLM Provider (choose one)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
OLLAMA_BASE_URL=http://localhost:11434

# Default provider and model
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-5-20250929

# MCP Server
MCP_TRANSPORT=http
MCP_SERVER_URL=https://your-mcp-server.example.com
MCP_SSL_VERIFY=true

# Agent Memory (choose one backend)
# Option 1: Filesystem (local development)
MEMORY_BACKEND=filesystem

# Option 2: Redis (production)
#MEMORY_BACKEND=redis
#REDIS_URL=redis://localhost:6379
#MEMORY_SHALLOW=true
```

### Memory Configuration

K8SOps supports three storage backends for session management:

| Backend | Use Case | Persistence | Requirements |
|---------|----------|-------------|--------------|
| `memory` | Testing | None (lost on restart) | None |
| `filesystem` | Local development | JSONL files | None |
| `redis` | Production | Redis server | Redis instance |

#### Storage Backend Selection

| Variable | Default | Description |
|----------|---------|-------------|
| `MEMORY_BACKEND` | `memory` | Storage backend: `memory`, `filesystem`, or `redis`. |
| `MEMORY_FILESYSTEM_PATH` | `~/.k8sops` | Base path for filesystem storage (when `MEMORY_BACKEND=filesystem`). |
| `REDIS_URL` | (none) | Redis connection URL (required when `MEMORY_BACKEND=redis`). |
| `MEMORY_SHALLOW` | `false` | Use shallow checkpointer that only stores latest state. Recommended for production. |

#### Filesystem Backend

The filesystem backend provides local persistence without requiring Redis. Ideal for local development.

**How it works:**
- Active session uses in-memory checkpointer (MemorySaver) for fast performance
- Each message is persisted to JSONL file in real-time
- When switching sessions, conversation is restored from JSONL file

**Storage structure:**
```
~/.k8sops/
├── sessions.jsonl           # Session metadata index
└── sessions/
    └── <user_id>/
        └── <session_id>.jsonl   # Conversation messages
```

#### Redis Backend (Short-term Memory)

For production deployments with Redis:
- Conversation history preserved across pod restarts
- Session recovery after unexpected failures
- Memory sharing across multiple instances (with sticky sessions)

#### Long-term Memory

Learns from sessions and retrieves relevant context for future interactions:
- Extracts key facts about user's environment (clusters, namespaces, preferences)
- Stores session summaries and successful troubleshooting patterns
- Retrieves relevant memories via semantic search when starting new sessions
- Automatically summarizes conversations when approaching context window limit

| Variable | Default | Description |
|----------|---------|-------------|
| `MEMORY_LONG_TERM_ENABLED` | `false` | Enable long-term memory (requires `REDIS_URL`). |
| `EMBEDDING_PROVIDER` | `openai` | Provider for embeddings: `openai` or `ollama`. Note: Anthropic has no embeddings API. |
| `EMBEDDING_MODEL` | (auto) | Embedding model. Defaults: OpenAI=`text-embedding-3-small`, Ollama=`nomic-embed-text`. |
| `MEMORY_CONTEXT_THRESHOLD` | `0.75` | Fraction of context window that triggers summarization. |
| `MEMORY_MAX_CONTEXT_TOKENS` | `100000` | Maximum tokens before summarization. |
| `MEMORY_MAX_MEMORIES` | `5` | Number of memories to retrieve per search. |
| `MEMORY_USER_ID` | `default` | User ID for memory namespace (when no auth). |

**Example configurations:**

Local development (no Redis):
```bash
# Filesystem storage for local development
MEMORY_BACKEND=filesystem
MEMORY_FILESYSTEM_PATH=~/.k8sops
```

Production (with Redis):
```bash
# Redis storage for production
MEMORY_BACKEND=redis
REDIS_URL=redis://localhost:6379
MEMORY_SHALLOW=true

# Long-term memory (optional)
MEMORY_LONG_TERM_ENABLED=true
EMBEDDING_PROVIDER=openai
```

**How it works:**

```
Session Start:
  └─→ Retrieve relevant memories from previous sessions
  └─→ Include in agent's system prompt

During Session:
  └─→ Monitor token count
  └─→ If approaching limit: summarize older messages, store summary, continue

Session End:
  └─→ Extract key facts and learnings
  └─→ Store as semantic/episodic memories for future retrieval
```

#### Multi-Session Support

K8SOps supports multiple persistent chat sessions (requires `filesystem` or `redis` backend):

- View list of past conversations in a sidebar
- Switch between conversations
- Create new conversations
- Delete old conversations
- Sessions persist across browser restarts

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_SESSIONS` | `10` | Maximum number of sessions to keep per user. Oldest sessions are auto-deleted when limit is exceeded. |

**How it works:**

```
┌─────────────────┬──────────────────────────────────────────────┐
│ Session Sidebar │  Main Chat Area                              │
├─────────────────│                                              │
│ [+ New Chat]    │  Messages...                                 │
│─────────────────│                                              │
│ > Current chat  │                                              │
│   Previous chat │                                              │
│   Older chat    │                                              │
└─────────────────┴──────────────────────────────────────────────┘
```

Session metadata (title, timestamps) stored separately from conversation history.
Auto-generates title from first user message.

### Run

```bash
reflex run
```

Open http://localhost:3000

## Testing

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests (requires MCP server)
pytest tests/integration/ -v

# E2E tests (requires app running)
pytest tests/e2e/ -v
```

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| AgentSession (core) | UI-agnostic session management enables CLI, tests, future interfaces |
| Checkpointer preserved | Conversation history maintained across model switches |
| Config from YAML | Add models without code changes |
| Single MCP server | Simpler than multi-server; tools discovered dynamically |
| Reflex UI | Proper async, WebSocket streaming, production React output |
| LangGraph | `astream_events()` for real-time streaming, built-in ReAct |

## References

- [Reflex Documentation](https://reflex.dev/docs/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [MCP Protocol Specification](https://spec.modelcontextprotocol.io/)
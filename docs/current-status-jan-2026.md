# K8SOps Agent - Current Status (January 2026)

## Quick Start for Continuing Development

This document captures the current state of the K8SOps Agent implementation as of January 1, 2026. Use this to understand the architecture, current progress, and where to continue development.

---

## Project Overview

**K8SOps** is a Python-based AI assistant for managing Kubernetes clusters. It provides a chat interface where users can ask questions about their cluster, and an AI agent uses MCP (Model Context Protocol) tools to execute kubectl, helm, and argocd commands.

### Architecture: Four Layers

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
│  - MemorySaver checkpointer (preserved across model switches)│
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
│  - Deployed at: cbx-mcp-k8s.vvklab.cloud.cembryonix.com    │
└─────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
./
├── .env                        # Environment configuration
├── .env.example                # Template for .env
├── .gitignore                  # Comprehensive Python + Reflex ignores
├── pyproject.toml              # Dependencies with pinned versions
├── rxconfig.py                 # Reflex config (app_name="k8sops")
├── README.md
│
├── k8sops/                     # Main package
│   ├── __init__.py             # Exports AgentSession, SessionSettings
│   ├── k8sops.py               # Reflex entry point
│   ├── session.py              # AgentSession - CORE session management
│   │
│   ├── ui/                     # UI Layer (Reflex) - Thin wrapper
│   │   ├── app.py              # rx.App definition
│   │   ├── styles.py           # Global styles
│   │   ├── state/
│   │   │   ├── base.py         # BaseState (sidebar toggle)
│   │   │   ├── chat.py         # ChatState (wraps AgentSession)
│   │   │   ├── settings.py     # SettingsState (triggers agent reinit)
│   │   │   └── session_manager.py  # Maps UI tokens to AgentSession
│   │   ├── components/
│   │   │   ├── chat/           # Message bubbles, input bar
│   │   │   ├── sidebar/        # Settings panel with dynamic dropdowns
│   │   │   └── tool_panel/     # Tool call visualization
│   │   └── pages/
│   │       └── index.py        # Main page layout
│   │
│   ├── agent/                  # Agent Layer (LangGraph)
│   │   ├── factory.py          # create_agent(), create_agent_with_mcp()
│   │   └── prompts/            # System prompts
│   │
│   ├── mcp_client/             # MCP Client Layer
│   │   └── client.py           # MCPClient class
│   │
│   ├── models/                 # LLM Providers
│   │   └── factory.py          # create_model() - Anthropic/OpenAI/Ollama
│   │
│   └── config/                 # Configuration
│       ├── __init__.py         # Exports settings and loader functions
│       ├── settings.py         # Pydantic settings (from .env)
│       ├── loader.py           # YAML config loader
│       └── defaults/           # Built-in defaults (YAML)
│           ├── models.yaml     # Provider/model definitions
│           └── settings.yaml   # App default settings
│
├── tests/                      # Test suite (reorganized)
│   ├── conftest.py             # Shared fixtures
│   ├── unit/                   # Unit tests (no external deps)
│   │   └── test_state.py       # State attribute tests
│   ├── integration/            # Integration tests
│   │   ├── conftest.py         # MCP fixtures
│   │   ├── test_mcp_client.py  # MCP client tests (read-only.yaml)
│   │   └── test_agent.py       # Agent tests (agent-*.yaml)
│   ├── e2e/                    # End-to-end (Playwright)
│   │   ├── test_ui.py          # Browser tests (loads from YAML)
│   │   └── test-cases/
│   │       └── ui-tests.yaml   # UI test definitions
│   ├── validation/             # Agent Q&A validation
│   │   ├── test_agent_qa.py    # Feed agent K8s questions
│   │   └── test-cases/
│   │       ├── agent-*.yaml    # Agent test cases
│   │       └── read-only.yaml  # MCP tool tests
│   └── standalone/             # Debug scripts (not pytest)
│       └── debug_*.py
│
├── ui-design/                  # UI Prototype (standalone)
│   └── ...
│
├── docs/
│   └── current-status-jan-2026.md  # This file
│
└── v1/                         # Archived old code (Chainlit-based)
```

---

## Key Implementation Details

### 1. AgentSession (Core)

**The heart of the system** - UI-agnostic session management that can be used by Reflex UI, future CLI, or tests.

```python
# k8sops/session.py
class AgentSession:
    def __init__(self, session_id: str = None, settings: SessionSettings = None):
        self.settings = settings or SessionSettings.from_env()
        self._checkpointer = None  # Preserved across model switches

    async def initialize(self):
        """Connect to MCP and create agent."""

    async def send_message(self, content: str) -> AsyncIterator[dict]:
        """Send message and stream response."""

    async def update_settings(self, **kwargs) -> bool:
        """Update settings, reinitialize agent if model changed.
        Returns True if agent was reinitialized."""

    async def cleanup(self):
        """Disconnect and cleanup."""
```

**Key Feature:** Checkpointer is preserved across model switches, so conversation history is maintained when you change models.

### 2. Settings Sync

When user changes provider/model in UI:
1. `SettingsState.set_provider()` updates state
2. Returns `ChatState.reinitialize_agent` event
3. `ChatState.reinitialize_agent()` calls `session.update_settings()`
4. `AgentSession` recreates agent with new model, same checkpointer
5. Conversation history is preserved

```python
# ui/state/settings.py
def set_provider(self, provider: str):
    self.llm_provider = provider
    self.model_name = get_default_model(provider)  # From config
    return ChatState.reinitialize_agent  # Trigger reinit
```

### 3. Configuration from YAML

Provider/model definitions loaded from `config/defaults/models.yaml`:

```yaml
# k8sops/config/defaults/models.yaml
providers:
  anthropic:
    name: "Anthropic"
    default_model: "claude-sonnet-4-20250514"
    models:
      - id: "claude-sonnet-4-20250514"
        name: "Claude Sonnet 4"
      - id: "claude-opus-4-20250514"
        name: "Claude Opus 4"
      # ...

  ollama:
    default_model: "qwen3:8b"
    models:
      - id: "qwen3:8b"
      - id: "qwen:7b"
      # ...
```

**To add a new model:** Just edit `models.yaml` - no Python changes needed.

**Helper functions:**
```python
from k8sops.config import get_providers, get_model_ids_for_provider, get_default_model

get_providers()  # ['anthropic', 'openai', 'ollama']
get_model_ids_for_provider('ollama')  # ['qwen3:8b', 'qwen:7b', ...]
get_default_model('ollama')  # 'qwen3:8b'
```

### 4. UI Layer (Reflex)

**Now a thin wrapper** around AgentSession:

```python
# ui/state/chat.py
class ChatState(rx.State):
    async def initialize(self):
        session = AgentSession(session_id=token)
        await session.initialize()
        session_manager.set_session(token, session)
        self._sync_from_session(session)

    async def send_message(self):
        session = self._get_session()
        async for event in session.send_message(user_message):
            # Handle events, update UI state
            yield
```

### 5. Test Structure

```
tests/
├── unit/           # Fast, no external deps
├── integration/    # MCP client + agent tests
├── e2e/            # Playwright browser tests (YAML-driven)
├── validation/     # Agent Q&A tests
└── standalone/     # Debug scripts
```

**E2E tests defined in YAML** (`tests/e2e/test-cases/ui-tests.yaml`):
```yaml
tests:
  - name: "page_loads"
    action: "navigate"
    expect:
      response_ok: true

  - name: "send_message"
    action: "interact"
    steps:
      - type: "fill"
        value: "What is 2+2?"
      - type: "wait_for_response"
        expect_any: ["4", "four"]
```

---

## Dependencies

```toml
# pyproject.toml
dependencies = [
    "reflex>=0.6.0",
    "langgraph==1.0.5",
    "langchain-core==1.2.5",
    "langchain-anthropic==1.3.0",
    "langchain-openai==1.1.6",
    "langchain-ollama==1.0.1",
    "mcp>=1.0.0",
    "langchain-mcp-adapters==0.2.1",
    "pydantic-settings>=2.0.0",
    "python-dotenv>=1.0.0",
    "httpx>=0.27.0",
    "pyyaml",
]
```

---

## Running the Application

```bash
pip install -e .
reflex run
```

Open http://localhost:3000

---

## Current Status

### Completed

- [x] Project restructured: renamed to `k8sops`, files at root
- [x] **AgentSession** - Core session management, UI-agnostic
- [x] **Settings sync** - Model changes reinitialize agent automatically
- [x] **Conversation preserved** - Checkpointer maintained across model switches
- [x] **Config from YAML** - Providers/models in `config/defaults/models.yaml`
- [x] UI separated from backend (thin wrapper around AgentSession)
- [x] UI prototype in `ui-design/` for layout experimentation
- [x] Dynamic settings panel (provider dropdown, model dropdown from config)
- [x] Fixed sidebar with Claude.ai-style layout
- [x] MCP client with dynamic tool discovery
- [x] Agent factory with LangGraph ReAct
- [x] Real-time streaming (token-by-token)
- [x] Tool call visualization
- [x] **Test reorganization** - unit, integration, e2e, validation, standalone
- [x] **E2E tests in YAML** - Non-developers can modify test definitions
- [x] Dependencies pinned (including langchain-ollama==1.0.1)
- [x] v1 code archived

### Known Issues / TODOs

1. **Multiline input** - Currently single-line. Shift+Enter for newline requires JS.
2. **MCP reconnect** - Needs reconnect button when server disconnects.
3. **Error recovery** - Better handling when MCP server errors.
4. **Tool output formatting** - Long JSON outputs could be formatted better.

### Future Ideas

1. **Multi-Model Architecture** - Provide agent with multiple models, let it choose:
   - **Router pattern**: Small model decides which model to use
   - **Multi-agent**: Supervisor delegates to specialized agents
   - **Use cases**:
     - Cost optimization (cheap model for simple, expensive for complex)
     - Speed vs depth (fast for status, slow for troubleshooting)
     - Privacy (local Ollama for sensitive data)

2. **CLI Interface** - Interactive terminal app (like Claude Code):
   - Uses same AgentSession (already UI-agnostic)
   - `/model ollama/qwen3:8b` to switch models
   - `/settings` to view/change configuration

3. **Persistent Sessions** - Save/restore conversation across restarts:
   - Replace MemorySaver with persistent checkpointer
   - Redis or SQLite backend

---

## Key Architectural Decisions

| Decision | Rationale |
|----------|-----------|
| **AgentSession (core)** | UI-agnostic session management. Enables CLI, tests, future interfaces. |
| **Checkpointer preserved** | Conversation history maintained across model switches. |
| **Config from YAML** | Add models without code changes. Easy for non-developers. |
| **Single MCP server** | Simpler than multi-server. Tools discovered dynamically. |
| **Reflex (not Chainlit)** | Proper async, WebSocket streaming, production React output. |
| **LangGraph** | `astream_events()` for real-time streaming, built-in ReAct. |
| **UI as thin wrapper** | State management in AgentSession, not Reflex state. |

---

## Continuing Development

### To add new features:

1. **New model/provider** → Edit `config/defaults/models.yaml`
2. **New UI component** → Add to `k8sops/ui/components/`
3. **New tool support** → MCP server handles this (no client changes)
4. **CLI interface** → Create `k8sops/cli/` using AgentSession directly

### To debug:

1. **UI issues** → Use `ui-design/` prototype to isolate
2. **Session issues** → Check AgentSession directly in Python
3. **Agent issues** → Run `tests/integration/test_agent.py`
4. **MCP issues** → Run `tests/integration/test_mcp_client.py`

### To test:

```bash
# Unit tests
python -m pytest tests/unit/ -v

# Integration tests (requires MCP server)
python tests/integration/test_mcp_client.py
python tests/integration/test_agent.py

# E2E tests (requires app running)
python tests/e2e/test_ui.py --visible

# Validation tests (requires app running)
python tests/validation/test_agent_qa.py
```

---

## References

- **MCP Protocol:** 2025-11-25 spec
- **Reflex Docs:** https://reflex.dev/docs/
- **LangGraph Docs:** https://langchain-ai.github.io/langgraph/
- **Sister Project:** cbx-mcp-server-k8s (MCP server implementation)

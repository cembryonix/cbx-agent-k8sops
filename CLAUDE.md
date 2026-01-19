# K8SOps Agent - Instructions for AI Assistants

## Project Overview

K8SOps is a Kubernetes operations AI assistant with Reflex UI, LangGraph agent, and MCP client. Ignore the `v1/` directory - it's archived legacy code.

## Tech Stack

- **UI**: Reflex (Python web framework, compiles to React)
- **Agent**: LangGraph ReAct agent with streaming
- **LLM**: Anthropic, OpenAI, or Ollama (configurable)
- **Tools**: MCP (Model Context Protocol) for kubectl/helm/argocd
- **Config**: Pydantic settings + YAML defaults

## Key Files

| File | Purpose |
|------|---------|
| `k8sops/session/` | Session management submodule |
| `k8sops/session/agent_session.py` | Core AgentSession - UI-agnostic session logic |
| `k8sops/session/store.py` | SessionStore - Redis-backed session metadata |
| `k8sops/ui/state/chat.py` | ChatState - Reflex UI state |
| `k8sops/ui/state/settings.py` | SettingsState - model/provider selection |
| `k8sops/agent/factory.py` | LangGraph agent creation |
| `k8sops/mcp_client/client.py` | MCP server connection |
| `k8sops/models/factory.py` | LLM provider abstraction |
| `k8sops/config/defaults/models.yaml` | Provider/model catalog |

## Common Tasks

### Add a new LLM model
Edit `k8sops/config/defaults/models.yaml` - no Python changes needed.

### Add UI component
Create in `k8sops/ui/components/`, import in relevant page.

### Modify agent behavior
Edit `k8sops/agent/prompts.py` for system prompt changes.

### Change default settings
Edit `k8sops/config/defaults/settings.yaml` or set environment variables.

## Running

```bash
# Start app
reflex run

# Run tests
pytest tests/unit/ -v
pytest tests/integration/ -v
```

## Architecture Rules

1. **AgentSession is UI-agnostic** - Don't add Reflex imports to `k8sops/session/`
2. **UI is thin wrapper** - Business logic belongs in AgentSession, not ChatState
3. **Config from YAML** - Avoid hardcoding model names in Python
4. **Checkpointer preserved** - Model switches must not reset conversation history

## Code Style

Follow [PEP 8](https://peps.python.org/pep-0008/) with these key points:

### Imports
- All imports at the top of the file, after module docstring
- Group in order: standard library → third-party → local application
- One import per line; avoid wildcard imports (`from x import *`)

### Formatting
- 4 spaces for indentation (no tabs)
- Max line length: 79 characters (72 for docstrings/comments)
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
- `mcp`, `langchain-mcp-adapters` - Tool integration
- `pydantic-settings` - Configuration

## Environment Variables

Required in `.env`:
- `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` or `OLLAMA_BASE_URL`
- `MCP_SERVER_URL` - MCP server endpoint
- `MCP_TRANSPORT` - `http` or `stdio`
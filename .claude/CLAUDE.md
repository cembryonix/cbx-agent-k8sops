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
| `k8sops/session.py` | Core AgentSession - UI-agnostic session logic |
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

1. **AgentSession is UI-agnostic** - Don't add Reflex imports to `session.py`
2. **UI is thin wrapper** - Business logic belongs in AgentSession, not ChatState
3. **Config from YAML** - Avoid hardcoding model names in Python
4. **Checkpointer preserved** - Model switches must not reset conversation history

## Code Style

- No leading underscores for module-level variables
- Use type hints
- Async/await for all I/O operations
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
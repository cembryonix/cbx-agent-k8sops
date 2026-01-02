# K8S Ops Agent v2

AI-powered Kubernetes operations assistant with Reflex UI, LangGraph agent, and MCP tool integration.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Reflex UI                            │
│   (Chat interface, tool visualization, settings)         │
└─────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────┐
│                  LangGraph Agent                         │
│   (ReAct agent with streaming, memory)                   │
└─────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────┐
│                  MCP Client Layer                        │
│   (Dynamic tool discovery, single server connection)     │
└─────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────┐
│                  MCP-K8S Server                          │
│   (kubectl, helm, argocd tools)                          │
└─────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Setup Environment

```bash
cd v2/k8s_ops_agent

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Copy environment template
cp .env.example .env
# Edit .env with your API keys and MCP server URL
```

### 2. Configure Environment

Edit `.env`:

```bash
# LLM Provider
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...

# MCP Server (your deployed server)
MCP_TRANSPORT=http
MCP_SERVER_URL=http://your-mcp-server:8080/mcp
```

### 3. Run the Application

```bash
reflex run
```

Open http://localhost:3000 in your browser.

## Project Structure

```
k8s_ops_agent/
├── rxconfig.py              # Reflex configuration
├── pyproject.toml           # Dependencies
├── .env                     # Environment variables
│
├── k8s_ops_agent/           # UI Layer (Reflex)
│   ├── state/               # State management
│   ├── components/          # UI components
│   ├── pages/               # Page definitions
│   └── k8s_ops_agent.py     # App entry point
│
├── agent/                   # Agent Layer (LangGraph)
│   ├── factory.py           # Agent creation
│   └── prompts.py           # System prompts
│
├── mcp_client/              # MCP Client Layer
│   └── client.py            # MCP connection & tool discovery
│
├── models/                  # LLM Providers
│   └── factory.py           # Model creation
│
└── config/                  # Configuration
    └── settings.py          # Pydantic settings
```

## Features

- **Dynamic Tool Discovery**: Tools are discovered from MCP server at runtime
- **Streaming Responses**: Real-time token streaming from LLM
- **Tool Call Visualization**: See tool invocations and outputs
- **Multiple LLM Providers**: Anthropic, OpenAI, Ollama
- **Dark Mode**: Default dark theme with toggle

## Development

```bash
# Run in development mode
reflex run

# Run tests
pytest

# Format code
ruff format .
ruff check --fix .
```

## Key Differences from v1

| Aspect | v1 (Chainlit) | v2 (Reflex) |
|--------|---------------|-------------|
| UI Framework | Chainlit | Reflex |
| Event Loop | Conflicting loops | Single event loop |
| MCP Client | Multi-server | Single server |
| Tool Discovery | Hardcoded | Dynamic |
| Streaming | SSE (issues in K8s) | WebSocket |

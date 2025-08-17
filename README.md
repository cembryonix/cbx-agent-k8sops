# CBX Agent: K8SOps ![status](https://img.shields.io/badge/status-early--development-orange)

> [!IMPORTANT]
> **STATUS: Early Development**
>
> Currently, the project provides only basic functionality.  
> Immediate focus of development is on optimizing choice of LLMs, prompts, deployment methods, and documentation.

**An AI companion for Kubernetes operations and troubleshooting.**
Part of the "Cembryonix Project" collection.

Transform your cluster management from command-line tasks to natural conversations.

## What it does

This AI agent is your conversational companion for Kubernetes operations. 
Simply describe what you need and it handles the kubectl, helm, and ArgoCD commands for you. 
From diagnosing pod failures to scaling deployments, it takes care of the command-line work 
while you focus on the bigger picture.

## Prerequisites

**Required:**
- Docker with Compose support (use `docker compose` or `docker-compose`)
- OpenAI API key (get from https://platform.openai.com/api-keys)  
- Working kubeconfig file with access to your Kubernetes cluster

**Kubernetes Configuration:**
- **Default**: `~/.kube/config`
- **Override**: Set `CBX_MCP_KUBECONFIG_DIR` in .env

**ArgoCD Configuration (Optional):**
- **Default**: `~/.config/argocd`
- **Override**: Set `CBX_MCP_ARGOCD_CONFIG_DIR` in .env

**Directory Structure Expected:**
```
~/.kube/
  └── config                    # Kubernetes cluster configuration

~/.config/argocd/              # ArgoCD configuration (optional)
  ├── config                   # ArgoCD server connections
  └── [other argocd files]
```

**Notes:**
- The startup script will check if these directories exist before starting containers
- CLI tools (kubectl, argocd) are validated at runtime - broken tools won't be available in the agent
- All configuration directories are mounted read-only for security


## Quick Start

1. **Get the code and navigate to quickstart:**
   ```bash
   git clone https://github.com/your-org/cbx-agent-k8sops.git
   cd cbx-agent-k8sops/quickstart/docker-compose
   ```

2. **Configure your environment:**
   ```bash
   cp .env.example .env
   # Edit .env to add your OpenAI API key
   # Optionally adjust kubectl/ArgoCD config directories
   ```

3. **Start the services:**
   ```bash
   ./run-compose.sh up
   ```
   The agent will be available at `http://localhost:8000`

4. **Stop when done:**
   ```bash
   ./run-compose.sh down
   ```

**What's running:**
- AI Agent (Chainlit UI) on port 8000
- MCP Server (K8s tools) on port 8080

## Using the Agent

**Note:** Until you get comfortable with the agent and LLM model behavior, 
it's safer to provide CLI credentials with restricted permissions.

Talk to your cluster like you would a colleague:

- "Something's wrong with the acme-api service - can you check it out?"
- "Scale up the frontend, we're getting more traffic"
- "Are all our ArgoCD apps synced properly?"

The agent translates your requests into the right kubectl, helm, and ArgoCD commands. 
You'll see every command it executes.

## Next Steps

**Documentation:**
- [Configuration Guide](docs/configuration.md) - Environment variables and advanced settings
- [Troubleshooting](docs/troubleshooting.md) - Common issues and solutions
- [Architecture Overview](docs/architecture.md) - How the AI agent and MCP server work together

**Development:**
- [Local Development](docs/development.md) - Setting up your development environment


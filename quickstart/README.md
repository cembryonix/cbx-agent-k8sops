# CBX Agent K8SOps - Quick Start

Quick deployment guide for trying out CBX Agent K8SOps with MCP server.

## Prerequisites

- Kubernetes cluster with kubectl access
- Helm 3.x installed
- OpenAI API key

## What to Edit

1. **Replace domain names** in the helm command:
   - `cbx-agent.yourdomain.com` → your actual domain
   - `cbx-mcp.yourdomain.com` → your actual domain

2. **Replace API key** in the secret creation:
   - `your-openai-api-key-here` → your actual OpenAI API key

## Helm Install

```bash
# Create namespace and secrets
kubectl create namespace cbx-agents
kubectl create secret generic cbx-agent-k8sops-openai-key \
  --from-literal=api-key="your-openai-api-key-here" \
  -n cbx-agents
kubectl create secret generic cbx-mcp-k8s-kubeconfig \
  --from-file=kubeconfig=~/.kube/config \
  -n cbx-agents

# Deploy
helm install cbx-agent pkg/helm/cbx-agent-k8sops \
  --namespace cbx-agents \
  --set agent.ingress.host=cbx-agent.yourdomain.com \
  --set cbx-mcp-server-k8s.ingress.host=cbx-mcp.yourdomain.com
```

## Access

- **Agent UI**: `http://cbx-agent.yourdomain.com`
- **MCP Server**: `http://cbx-mcp.yourdomain.com/mcp/`

For detailed installation options and troubleshooting, see [Installation Guide](../docs/installation.md).

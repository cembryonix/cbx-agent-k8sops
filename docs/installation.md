# CBX K8S agent installation

## Introduction

This guide covers installation methods for CBX Agent K8SOps.

## Local install 

### Docker-Compose

### Two Apps wth stdio transport

## Kubernetes install

The CBX Agent K8SOps can be deployed using Helm with or without the MCP server. CBX-MCP-K8S server is needed for the agent to function but can be deployed separately and agent can be configured to use the pre-existing MCP server 

### Prerequisites

#### Required
- Kubernetes cluster with kubectl access
- Helm 3.x installed
- OpenAI API key (get from https://platform.openai.com/api-keys)

#### Optional
- ArgoCD CLI and configuration (for ArgoCD operations)
- Working kubeconfig with cluster access

### Deployment Options

#### Option 1: Deploy Both Agent and MCP Server (Recommended)

This is the simplest approach for most users - deploys both the agent and MCP server together.

```bash
# Clone the repository
git clone https://github.com/cembryonix/cbx-agent-k8sops.git
cd cbx-agent-k8sops

# Create required secrets first
kubectl create namespace cbx-agents

# Create OpenAI API key secret
kubectl create secret generic cbx-agent-k8sops-openai-key \
  --from-literal=api-key="your-openai-api-key-here" \
  -n cbx-agents

# Create Anthropic API key secret (optional)
kubectl create secret generic cbx-agent-k8sops-anthropic-key \
  --from-literal=api-key="your-anthropic-api-key-here" \
  -n cbx-agents

# Create kubeconfig secret for MCP server
kubectl create secret generic cbx-mcp-k8s-kubeconfig \
  --from-file=kubeconfig=~/.kube/config \
  -n cbx-agents

# Create ArgoCD config secret (optional)
kubectl create secret generic cbx-mcp-k8s-argocd-config \
  --from-file=config=~/.config/argocd/config \
  -n cbx-agents

# Deploy both agent and MCP server
helm install cbx-agent pkg/helm/cbx-agent-k8sops \
  --namespace cbx-agents \
  --set agent.ingress.host=cbx-agent.yourdomain.com \
  --set cbx-mcp-server-k8s.ingress.host=cbx-mcp.yourdomain.com
```

#### Option 2: Deploy Agent Only

Deploy just the agent without the MCP server (useful if you have an external MCP server).

```bash
# Deploy agent only
helm install cbx-agent pkg/helm/cbx-agent-k8sops \
  --namespace cbx-agents \
  --set mcp_included=false \
  --set agent.ingress.host=cbx-agent.yourdomain.com
```

#### Option 3: Deploy MCP Server Standalone

Deploy the MCP server independently (useful for serving multiple agents).

```bash
# Deploy MCP server only
helm install cbx-mcp-server pkg/helm/cbx-mcp-server-k8s \
  --namespace cbx-agents \
  --set ingress.host=cbx-mcp.yourdomain.com
```

#### Option 4: Deploy with Custom Configuration

Customize the deployment with your own settings.

```bash
# Deploy with custom configuration
helm install cbx-agent pkg/helm/cbx-agent-k8sops \
  --namespace cbx-agents \
  --set agent.ingress.host=cbx-agent.yourdomain.com \
  --set cbx-mcp-server-k8s.ingress.host=cbx-mcp.yourdomain.com \
  --set agent.config.configYaml="default_model: openai/gpt-4\ntemperature: 0.1" \
  --set agent.resources.limits.cpu=2000m \
  --set agent.resources.limits.memory=2Gi
```

### Configuration

#### Required Secrets

Before deploying, you must create these secrets in your Kubernetes cluster:

##### OpenAI API Key
```bash
kubectl create secret generic cbx-agent-k8sops-openai-key \
  --from-literal=api-key="your-openai-api-key-here" \
  -n cbx-agents
```

##### Anthropic API Key (Optional)
```bash
kubectl create secret generic cbx-agent-k8sops-anthropic-key \
  --from-literal=api-key="your-anthropic-api-key-here" \
  -n cbx-agents
```

##### Kubeconfig for MCP Server
```bash
kubectl create secret generic cbx-mcp-k8s-kubeconfig \
  --from-file=kubeconfig=~/.kube/config \
  -n cbx-agents
```

##### ArgoCD Config for MCP Server (Optional)
```bash
kubectl create secret generic cbx-mcp-k8s-argocd-config \
  --from-file=config=~/.config/argocd/config \
  -n cbx-agents
```

#### Ingress Configuration

Update the ingress hosts to match your domain:

```bash
# For agent
--set agent.ingress.host=cbx-agent.yourdomain.com

# For MCP server
--set cbx-mcp-server-k8s.ingress.host=cbx-mcp.yourdomain.com
```

### Verification

#### Check Deployment Status
```bash
# Check all resources
kubectl get all -n cbx-agents

# Check pods
kubectl get pods -n cbx-agents

# Check services
kubectl get svc -n cbx-agents

# Check ingress
kubectl get ingress -n cbx-agents
```

#### Check Pod Logs
```bash
# Agent logs
kubectl logs -f deployment/cbx-agent-cbx-agent-k8sops -n cbx-agents

# MCP server logs (if deployed)
kubectl logs -f deployment/cbx-agent-cbx-mcp-server-k8s -n cbx-agents
```

#### Access the Application

Once deployed, you can access:

- **Agent UI**: `http://cbx-agent.yourdomain.com`
- **MCP Server**: `http://cbx-mcp.yourdomain.com/mcp/`

### Management

#### Upgrade Deployment
```bash
# Update dependencies first
helm dependency update pkg/helm/cbx-agent-k8sops

# Upgrade deployment
helm upgrade cbx-agent pkg/helm/cbx-agent-k8sops \
  --namespace cbx-agents
```

#### Uninstall
```bash
# Remove the deployment
helm uninstall cbx-agent -n cbx-agents

# Remove secrets (optional)
kubectl delete secret cbx-agent-k8sops-openai-key -n cbx-agents
kubectl delete secret cbx-agent-k8sops-anthropic-key -n cbx-agents
kubectl delete secret cbx-mcp-k8s-kubeconfig -n cbx-agents
kubectl delete secret cbx-mcp-k8s-argocd-config -n cbx-agents
```

### Troubleshooting

#### Common Issues

##### Pod Not Starting
```bash
# Check pod status
kubectl describe pod <pod-name> -n cbx-agents

# Check events
kubectl get events -n cbx-agents --sort-by='.lastTimestamp'
```

##### Missing Secrets
```bash
# Verify secrets exist
kubectl get secrets -n cbx-agents

# Check secret contents
kubectl get secret cbx-agent-k8sops-openai-key -n cbx-agents -o yaml
```

##### Ingress Not Working
```bash
# Check ingress status
kubectl describe ingress -n cbx-agents

# Verify ingress controller is running
kubectl get pods -n ingress-nginx
```

#### Getting Help

- Check the [main documentation](./)
- Review [troubleshooting guide](./troubleshooting.md)
- Open an issue on GitHub

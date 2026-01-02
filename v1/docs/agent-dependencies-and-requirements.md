# CBX Agent K8sOps - Dependencies & Requirements

This document outlines all the dependency resources and requirements needed for the cbx-agent-k8sops to work properly in a Kubernetes cluster.

## 🔧 Required Kubernetes Resources

### 1. Secrets (Must exist before deployment)

The agent requires these secrets to be created manually:

```bash
# OpenAI API Key Secret
kubectl create secret generic cbx-agent-k8sops-openai-key \
  --from-literal=api-key="YOUR_OPENAI_API_KEY" \
  -n cbx-agents

# Anthropic API Key Secret  
kubectl create secret generic cbx-agent-k8sops-anthropic-key \
  --from-literal=api-key="YOUR_ANTHROPIC_API_KEY" \
  -n cbx-agents
```

**Secret Requirements:**
- **Namespace:** `cbx-agents` (or target deployment namespace)
- **Secret Names:** Must match values in `agent.secretReferences`
- **Key Names:** Must be `api-key` for both secrets

### 2. Namespace

```bash
# Create namespace if it doesn't exist
kubectl create namespace cbx-agents
```

## 🌐 Network & Infrastructure Requirements

### 3. Ingress Controller

The cluster must have an nginx ingress controller installed:

```bash
# Check if nginx ingress exists
kubectl get pods -n ingress
kubectl get svc -n ingress

# Should see nginx-ingress service with LoadBalancer/External IP
```

### 4. DNS Configuration

Domain must resolve to the ingress controller's external IP:

```bash
# Your domain should resolve to ingress IP
nslookup cbx-agent-k8sops.vvklab.cloud.cembryonix.com
# Should return the ingress LoadBalancer IP (e.g., 10.0.0.200)
```

## 🤖 MCP Server Dependency

### 5. MCP Server Options

**Option A: Same Cluster (Default/Recommended)**
```yaml
# Uses internal service communication
mcpConfig:
  servers:
    k8s_mcp:
      url: "http://cbx-mcp-k8s.cbx-mcp-servers.svc.cluster.local:8080/mcp/"
      transport: "streamable_http"
```

**Option B: External MCP Server**
```yaml
# Uses external URL
mcpConfig:
  servers:
    k8s_mcp:
      url: "http://your-external-mcp-server.com:8080/mcp/"
      transport: "streamable_http"
```

**Option C: Different Cluster Service**
```yaml
# Different service name/namespace
mcpConfig:
  servers:
    k8s_mcp:
      url: "http://YOUR-MCP-SERVICE.YOUR-NAMESPACE.svc.cluster.local:8080/mcp/"
      transport: "streamable_http"
```

## 📋 Complete Pre-Installation Checklist

### Required Before Helm Install:

```bash
# 1. Create namespace
kubectl create namespace cbx-agents

# 2. Create required secrets
kubectl create secret generic cbx-agent-k8sops-openai-key \
  --from-literal=api-key="sk-your-openai-key" \
  -n cbx-agents

kubectl create secret generic cbx-agent-k8sops-anthropic-key \
  --from-literal=api-key="your-anthropic-key" \
  -n cbx-agents

# 3. Verify ingress controller
kubectl get svc -n ingress nginx-ingress

# 4. Configure DNS (external DNS provider)
# Point cbx-agent-k8sops.your-domain.com → INGRESS_EXTERNAL_IP

# 5. Ensure MCP server is available (if using same cluster)
kubectl get svc -n cbx-mcp-servers cbx-mcp-k8s
```

### Verification Commands:

```bash
# Verify all dependencies before install
kubectl get secrets -n cbx-agents | grep cbx-agent-k8sops
kubectl get svc -n ingress
nslookup cbx-agent-k8sops.your-domain.com
kubectl get svc -n cbx-mcp-servers  # if using same cluster
```

## 🎯 Minimal Installation Example

**Create all dependencies:**
```bash
# Step 1: Create namespace and secrets
kubectl create namespace cbx-agents
kubectl create secret generic cbx-agent-k8sops-openai-key \
  --from-literal=api-key="YOUR_KEY" -n cbx-agents
kubectl create secret generic cbx-agent-k8sops-anthropic-key \
  --from-literal=api-key="YOUR_KEY" -n cbx-agents

# Step 2: Install with custom values
helm install cbx-agent-k8sops ./cbx-agent-k8sops \
  -n cbx-agents \
  -f values-agent.yaml
```

## ⚠️ Common Issues & Solutions

### If secrets don't exist:
```
Error: couldn't find key api-key in Secret cbx-agents/cbx-agent-k8sops-openai-key
```
**Solution:** Create the required secrets using the commands in section 1.

### If ingress controller missing:
```
Warning: networking.k8s.io/v1beta1 Ingress is deprecated in v1.19+
```
**Solution:** Install nginx ingress controller in your cluster.

### If MCP server not accessible:
```
Connection failed: Could not resolve hostname cbx-mcp-k8s.cbx-mcp-servers.svc.cluster.local
```
**Solution:** Ensure MCP server is deployed or update `mcpConfig.servers.k8s_mcp.url` to correct address.

### If DNS not configured:
```
curl: (6) Could not resolve host: cbx-agent-k8sops.your-domain.com
```
**Solution:** Configure DNS records to point your domain to the ingress controller's external IP.

## 📚 Additional Notes

- The agent uses Chainlit for the web interface
- OpenAI and Anthropic API keys are both supported
- The MCP server provides Kubernetes operations capabilities
- All components can run in the same cluster for optimal performance
- External MCP servers are supported for distributed deployments

For more information, refer to the Helm chart documentation and configuration examples.
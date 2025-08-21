# Helm Chart MCP Server Update Summary

## Overview
Updated the Helm chart to include optional MCP server deployment alongside the CBX Agent K8SOps.

## Changes Made

### 1. **values.yaml Updates**
- Added `mcp_included: true` flag (default: true)
- Added `mcpServer` section with complete configuration:
  - Image: `ghcr.io/cembryonix/cbx-mcp-server-k8s:v0.1.1`
  - Service: ClusterIP on port 8080
  - Ingress: `cbx-mcp-k8s.yourdomain.com/mcp/` with nginx class
  - Resource limits: Same as agent (1000m CPU, 1Gi memory)
  - Secret references for kubeconfig and argocd config
  - MCP server configuration file

### 2. **New Template Files**
- `templates/mcp-server-deployment.yaml` - MCP server deployment
- `templates/mcp-server-service.yaml` - MCP server service
- `templates/mcp-server-ingress.yaml` - MCP server ingress
- `templates/mcp-server-configmap.yaml` - MCP server configuration

### 3. **Updated Template Files**
- `templates/configmap.yaml` - Combined agent config and MCP config
- `templates/deployment.yaml` - Updated volume mounts for single ConfigMap
- `templates/configmap-mcp.yaml` - Deleted (merged into main ConfigMap)

### 4. **Key Features**

#### **Conditional Deployment**
- All MCP server templates use `{{- if .Values.mcp_included }}` conditionals
- When `mcp_included: false`, only agent is deployed
- When `mcp_included: true`, both agent and MCP server are deployed

#### **Dynamic MCP URL Configuration**
- When MCP server is included, agent's MCP config automatically points to internal service
- Users can override by providing custom `mcpConfigJson` in values.yaml
- Service name follows Helm naming convention: `{{ include "cbx-agent-k8sops.fullname" . }}-mcp-server`

#### **Secret Management**
- Kubeconfig secret: `cbx-mcp-k8s-kubeconfig` (key: `kubeconfig`)
- ArgoCD config secret: `cbx-mcp-k8s-argocd-config` (key: `config`)
- Both secrets must be pre-existing before deployment
- Mounted as read-only volumes in MCP server container

#### **Configuration Structure**
- Agent config: Single ConfigMap with `config.yaml` and `mcp_config.json` keys
- MCP server config: Separate ConfigMap with `mcp-config.yaml` key
- MCP config mounted at `/home/appuser/app_configs/mcp-config.yaml`

## Usage Examples

### Deploy with MCP Server (default)
```bash
helm install my-release pkg/helm/cbx-agent-k8sops
```

### Deploy without MCP Server
```bash
helm install my-release pkg/helm/cbx-agent-k8sops --set mcp_included=false
```

### Deploy with Custom MCP Server URL
```bash
helm install my-release pkg/helm/cbx-agent-k8sops \
  --set config.mcpConfigJson='{"mcp_servers":{"k8s_mcp":{"url":"http://external-mcp-server:8080/mcp/","transport":"streamable_http"}}}'
```

## Pre-requisites

### Required Secrets
```yaml
# Kubeconfig secret
apiVersion: v1
kind: Secret
metadata:
  name: cbx-mcp-k8s-kubeconfig
type: Opaque
data:
  kubeconfig: <base64-encoded-kubeconfig>

---
# ArgoCD config secret
apiVersion: v1
kind: Secret
metadata:
  name: cbx-mcp-k8s-argocd-config
type: Opaque
data:
  config: <base64-encoded-argocd-config>
```

### Required API Keys
- OpenAI API key secret: `cbx-agent-k8sops-openai-key`
- Anthropic API key secret: `cbx-agent-k8sops-anthropic-key`

## Network Access

### Internal Access
- Agent: `http://test-release-cbx-agent-k8sops:8000`
- MCP Server: `http://test-release-cbx-agent-k8sops-mcp-server:8080`

### External Access (via Ingress)
- Agent: `http://cbx-agent-k8sops.yourdomain.com`
- MCP Server: `http://cbx-mcp-k8s.yourdomain.com/mcp/`

## Testing

### Validate Templates
```bash
# Test with MCP server included
helm template test-release pkg/helm/cbx-agent-k8sops --set mcp_included=true

# Test without MCP server
helm template test-release pkg/helm/cbx-agent-k8sops --set mcp_included=false
```

## Notes
- Both images are public on GHCR, no credentials or image pull secrets required
- MCP server can be deployed standalone to serve other agents
- Agent can connect to external MCP servers by overriding the MCP config
- All configurations are customizable through values.yaml 
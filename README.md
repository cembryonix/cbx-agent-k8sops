# cbx-agent-k8sops

**Automated Kubernetes troubleshooting with a conversational interface.**
Part of the "Cembryonix Project" collection.

This K8SOps is an **agentic AI troubleshooting system** with the main goal to help DevOps engineers automatically diagnose and fix problems in Kubernetes clusters.

## Quick start

```bash
cd quickstart/docker-compose
cp .env.example .env

# Edit .env
# 1. to add API keys (currently only OpenAI's will be used)
# 2. Optionally uncomment and change config directories for kubectl and argocd CLIs

# Wrapper for "docker compose" to provide env vars for rendering docker-compose.yml
./run-compose.sh up

# To stop
./run-compose.sh down
```

## Misc Notes

### Versions

App tested with Python 3.12








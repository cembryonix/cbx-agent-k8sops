# cbx-agent-k8sops

Operations Agent to work with Kubernetes ( "Cembryonix Project" collection )

This K8SOps is an **agentic AI troubleshooting system** with the main goal to help devops engineers autonomously 
diagnose and fix problems in Kubernetes clusters.


## Quick start

```bash
cd quickstart/docker-compose
cp .env.example .env

# Edit .env 
# 1. to add API keys ( currently only OpenAI's will be used)
# 2. Optionally uncomment and change config directories for kubectl and argocd CLIs

# wrapper for "docker compose" to provide env vars for rendering docker-compose.yml
./run-compose.sh up

# to stop 
./run-compose.sh down


```




## Mics Notes:

### versions:

app tested with Python 3.12

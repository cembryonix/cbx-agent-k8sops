#!/bin/bash

set -e

get_ip() {
    if command -v ip >/dev/null 2>&1; then
        # Linux with ip command
        ip route get 1.1.1.1 2>/dev/null | awk '{print $7; exit}'
    else
        # macOS or Linux with ifconfig
        ifconfig | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1' | head -1 | awk '{print $2}' | sed 's/addr://'
    fi
}

# check where we are and set the root of repo
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# this script is in {root}/test/
root_dir="${script_dir}/.."

conf_dir="${script_dir}/conf_dirs/http_local"

# Set the working directory to the script's location
pushd $script_dir

# Load environment variables if .env exists
if [ -f .env ]; then
    echo "Loading environment variables from .env..."
    export $(cat .env | grep -v '#' | xargs)
fi

# Container settings
CONTAINER_NAME="cbx-agent-k8sops"
IMAGE_NAME="cbx-agent-k8sops:develop"
#IMAGE_NAME="ghcr.io/vkuusk/cbx-agent-k8sops:v0.1.0"
PORT="8000"

echo "🚀 Starting K8S-Ops AI container..."

# Stop existing container if running
if docker ps --format "table {{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
    echo "Stopping existing container..."
    docker stop "$CONTAINER_NAME"
    docker rm "$CONTAINER_NAME"
fi

MY_HOST_IP=$(get_ip)
# Generate MCP config from template
sed "s/MCP_SERVER_IP/$MY_HOST_IP/g" \
    "${conf_dir}/mcp_config.template.json" \
    > "${conf_dir}/mcp_config.json"

export K8SOPS_CONFIG_DIR="${conf_dir}"
# Start new container
docker run -d \
    --name "$CONTAINER_NAME" \
    --restart unless-stopped \
    -p "$PORT:8000" \
    -e PYTHONPATH="/app" \
    -e OPENAI_API_KEY=${OPENAI_API_KEY} \
    -e ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY} \
    -v "${K8SOPS_CONFIG_DIR:-~/.k8sops}:/root/.k8sops" \
    "$IMAGE_NAME"

echo "✅ K8SOps agent started."
echo "🌐 Access at: http://localhost:$PORT"
echo "📝 View logs: docker logs -f $CONTAINER_NAME"

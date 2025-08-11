#!/usr/bin/env bash

# check where we are and set the root of repo
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# this script is in {root}/examples/docker-compose/
root_dir="${script_dir}/../../"

conf_dir="${script_dir}/../conf_dirs/http_local"

###########
get_local_ip() {
    local ip

    if command -v ip >/dev/null 2>&1; then
        # Linux (modern)
        ip=$(ip -o -4 addr show up | awk '!/ lo / {print $4; exit}' | cut -d/ -f1)
    elif command -v ifconfig >/dev/null 2>&1; then
        # macOS or legacy Linux
        ip=$(ifconfig | awk '/flags=.*UP/ {iface=$1} /inet / && $2 != "127.0.0.1" {print $2; exit}')
    else
        echo "Neither 'ip' nor 'ifconfig' command is available" >&2
        return 1
    fi

    echo "$ip"
}

show_usage() {
    echo "Usage: $0 {up|down}"
    echo ""
    echo "Commands:"
    echo "  up    - compose UP"
    echo "  down  - compose DOWN"
    echo ""
}

setup_environment() {
    # Set the working directory to the script's location
    pushd $script_dir > /dev/null

    # Load environment variables if .env exists
    if [ -f .env ]; then
        echo "Loading environment variables from .env..."
        set -a  # automatically export all variables
        source .env
        set +a  # turn off automatic export
    fi

    # Set and export required variables
    MY_HOST_IP=$(get_local_ip)
    echo "Detected local IP: $MY_HOST_IP"

    # Generate MCP config from template (only needed for up command)
    if [ "$1" = "up" ]; then
        awk -v local_ip="$MY_HOST_IP" '{gsub(/MCP_SERVER_IP/, local_ip)} 1' \
          "${conf_dir}/mcp_config.template.json" \
          > "${conf_dir}/mcp_config.json"
    fi

    # Export application configuration
    export CBX_K8SOPS_CONFIG_DIR="${conf_dir}"
    export APP_IMAGE_NAME="ghcr.io/cembryonix/cbx-agent-k8sops:v0.1.1"
    export MCP_IMAGE_NAME="ghcr.io/cembryonix/cbx-mcp-server-k8s:v0.1.1"
    export APP_PORT=8000
    export MCP_PORT=8080

    # Handle UID/GID for Linux compatibility (use different variable names)
    export DOCKER_UID=$(id -u)
    export DOCKER_GID=$(id -g)

    # Set optional configuration directories with defaults for CLIs used by MCP server
    # These can be overridden in .env file
    export CBX_MCP_KUBECONFIG_DIR="${CBX_MCP_KUBECONFIG_DIR:-${HOME}/.kube}"
    export CBX_MCP_ARGOCD_CONFIG_DIR="${CBX_MCP_ARGOCD_CONFIG_DIR:-${HOME}/.config/argocd}"

    echo "Configuration:"
    echo "  APP_IMAGE_NAME: $APP_IMAGE_NAME"
    echo "  MCP_IMAGE_NAME: $MCP_IMAGE_NAME"
    echo "  APP_PORT: $APP_PORT"
    echo "  MCP_PORT: $MCP_PORT"
    echo "  CONFIG_DIR: $K8SOPS_CONFIG_DIR"
    echo "  DOCKER_UID: $DOCKER_UID"
    echo "  DOCKER_GID: $DOCKER_GID"
    echo "  MCP_KUBECONFIG_DIR: $CBX_MCP_KUBECONFIG_DIR"
    echo "  MCP_ARGOCD_CONFIG_DIR: $CBX_MCP_ARGOCD_CONFIG_DIR"
}

start_services() {
    echo "Starting K8SOps agent and MCP server..."
    if docker compose up -d; then
        echo "✅ K8SOps agent and MCP server started."
        echo "🌐 Access at: http://localhost:$APP_PORT"
        echo "📝 View logs: docker logs -f cbx-agent-k8sops"
        echo "🛑 Stop both services: '$0 down'"
    else
        echo "❌ Failed to start services"
        popd > /dev/null
        exit 1
    fi
}

stop_services() {
    echo "Stopping K8SOps agent and MCP server..."
    if docker compose down; then
        echo "✅ K8SOps agent and MCP server stopped."
    else
        echo "❌ Failed to stop services"
        popd > /dev/null
        exit 1
    fi
}

# let's do it
case "${1:-}" in
    up)
        setup_environment "up"
        start_services
        ;;
    down)
        setup_environment "down"
        stop_services
        ;;
    "")
        echo "❌ Error: No command specified"
        echo ""
        show_usage
        exit 1
        ;;
    *)
        echo "❌ Error: Unknown command '$1'"
        echo ""
        show_usage
        exit 1
        ;;
esac

popd > /dev/null
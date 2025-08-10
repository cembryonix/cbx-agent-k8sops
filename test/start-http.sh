#!/bin/bash

set -e

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

# CRITICAL: Add the project root to PYTHONPATH
export PYTHONPATH="${root_dir}:${PYTHONPATH}"
# Set Chainlit configuration path ( absolute )
export CHAINLIT_APP_ROOT="${root_dir}/app/k8sops/chainlit_cfg"

# Suppress async warnings (optional - uncomment if you want to suppress at script level)
# export PYTHONWARNINGS="ignore::RuntimeWarning:.*async generator ignored GeneratorExit.*,ignore::RuntimeWarning:.*Attempted to exit cancel scope.*"

# Check if virtual environment exists and activate it
if [ -d "${root_dir}/venv" ]; then
    echo "Activating virtual environment..."
    source ${root_dir}/venv/bin/activate
fi

MY_HOST_IP=$(get_local_ip)
# Generate MCP config from template
sed "s/MCP_SERVER_IP/$MY_HOST_IP/g" \
    "${conf_dir}/mcp_config.template.json" \
    > "${conf_dir}/mcp_config.json"

export K8SOPS_CONFIG_DIR="${conf_dir}"

echo "Starting Chainlit application..."
chainlit run ${root_dir}/app/main.py -w --host 0.0.0.0 --port 8000

popd

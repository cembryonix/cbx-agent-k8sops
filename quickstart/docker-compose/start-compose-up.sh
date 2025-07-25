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



# Set the working directory to the script's location
pushd $script_dir

# Load environment variables if .env exists. otherwise export by yourself
# # OpenAI API key
# export OPENAI_API_KEY="sk-proj-1234567890abcdef..."
# # Anthropic API key
# export ANTHROPIC_API_KEY="sk-ant-api03-..."

# note: docker compose will read .env by default anyway, so this is here just make it explicit
if [ -f .env ]; then
    echo "Loading environment variables from .env..."
    export $(cat .env | grep -v '#' | xargs)
fi

MY_HOST_IP=$(get_local_ip)
# Generate MCP config from template
awk -v local_ip="$MY_HOST_IP" '{gsub(/MCP_SERVER_IP/, local_ip)} 1' \
  "${conf_dir}/mcp_config.template.json" \
  > "${conf_dir}/mcp_config.json"

#
#sed "s/MCP_SERVER_IP/$MY_HOST_IP/g" \
#    "${conf_dir}/mcp_config.template.json" \
#    > "${conf_dir}/mcp_config.json"

export K8SOPS_CONFIG_DIR="${conf_dir}"

# not used in compose yet (hardcoded in docker-compose)
PORT=8000

if docker compose up -d; then
  echo "✅ K8SOps agent and MCP server started."
  echo "🌐 Access at: http://localhost:$PORT"
  echo "📝 View logs: docker logs -f $CONTAINER_NAME"
  echo "🛑 Stop both services: 'docker compose down'"
else
  echo "Failure"
fi

popd > /dev/null

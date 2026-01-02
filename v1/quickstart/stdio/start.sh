#!/bin/bash

# check if port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 1  # Port is in use
    else
        return 0  # Port is available
    fi
}

# find available port starting from provided port
find_available_port() {
    local start_port=$1
    local port=$start_port

    while [ $port -le $((start_port + 50)) ]; do
        if check_port $port; then
            echo $port
            return 0
        fi
        port=$((port + 1))
    done

    echo "ERROR: No available ports found between $start_port and $((start_port + 50))"
    return 1
}

# check where we are and set the root of repo
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# this script is in {root}/examples/local-stdio/
root_dir="${script_dir}/../../"

conf_dir="${script_dir}/../conf_dirs/stdio"

venv_dir_name="runtime_venv"

# default port
DEFAULT_PORT=8000

# Check if port is available, find alternative if not
echo "Checking port availability..."
if check_port $DEFAULT_PORT; then
    CHAINLIT_PORT=$DEFAULT_PORT
    echo "Port $DEFAULT_PORT is available"
else
    echo "Port $DEFAULT_PORT is in use, finding alternative..."
    CHAINLIT_PORT=$(find_available_port $DEFAULT_PORT)
    if [ $? -ne 0 ]; then
        echo "$CHAINLIT_PORT"  # This will be the error message
        exit 1
    fi
    echo "Using port $CHAINLIT_PORT instead"
fi

# Set the working directory to the script's location
pushd $script_dir

# load environment variables if .env exists
if [ -f .env ]; then
    echo "Loading environment variables from .env..."
    export $(cat .env | grep -v '#' | xargs)
fi

# Create and activate virtual environment if it doesn't exist
if [ ! -d ${venv_dir_name} ]; then
    echo "Creating virtual environment..."
    python3 -m venv ${venv_dir_name}

    echo "Activating virtual environment..."
    source ${venv_dir_name}/bin/activate

    # Upgrade pip first
    echo "Upgrading pip..."
    pip install --upgrade pip

    # Install requirements
    echo "Installing requirements..."
    pip install -r "${root_dir}/requirements.txt"
else
    echo "Activating existing virtual environment..."
    source ${venv_dir_name}/bin/activate
fi

# Verify chainlit is available
if ! command -v chainlit &> /dev/null; then
    echo "Error: chainlit not found in virtual environment. check requirements.txt"
    exit 1
fi

# add the project root to PYTHONPATH
export PYTHONPATH="${root_dir}:${PYTHONPATH}"
# set chainlit configuration path ( ! has to be absolute )
export CHAINLIT_APP_ROOT="${root_dir}/app/k8sops/chainlit_cfg"

# :-) tried to suppress async warnings. need uncomment to suppress at script level but for some reasons does not work :-)
# TODO: fix error in the first place
# export PYTHONWARNINGS="ignore::RuntimeWarning:.*async generator ignored GeneratorExit.*,ignore::RuntimeWarning:.*Attempted to exit cancel scope.*"

# Generate MCP config from template
awk -v home="$HOME" '{gsub(/MY_USER_HOME_DIR/, home)} 1' \
  "${conf_dir}/mcp_config.template.json" \
  > "${conf_dir}/mcp_config.json"

export K8SOPS_CONFIG_DIR="${conf_dir}"

echo "Starting Chainlit application on port $CHAINLIT_PORT..."
echo "Access your application at: http://localhost:$CHAINLIT_PORT"
chainlit run "${root_dir}/app/main.py" -w --host 0.0.0.0 --port $CHAINLIT_PORT

popd
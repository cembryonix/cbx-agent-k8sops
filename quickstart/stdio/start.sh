#!/bin/bash

# check where we are and set the root of repo
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# this script is in {root}/examples/local-stdio/
root_dir="${script_dir}/../../"

conf_dir="${script_dir}/../conf_dirs/stdio"

venv_dir_name="release_venv"

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

# Unzip virtual environment and activate it
unzip release_venv.zip
if [ -d ${venv_dir_name} ]; then
  echo "Activating virtual environment..."
  source ${venv_dir_name}/bin/activate
else
  echo "Error: no 'venv' directory. It's required to run the code. Exiting..."
  exit 1
fi


# Generate MCP config from template
awk -v home="$HOME" '{gsub(/MY_USER_HOME_DIR/, home)} 1' \
  "${conf_dir}/mcp_config.template.json" \
  > "${conf_dir}/mcp_config.json"


export K8SOPS_CONFIG_DIR="${conf_dir}"

echo "Starting Chainlit application..."
chainlit run "${root_dir}/app/main.py" -w --host 0.0.0.0 --port 8000

# cleanup venv dir
rm -rf ${venv_dir_name}

popd
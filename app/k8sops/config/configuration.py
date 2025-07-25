
import os
import json
import yaml

APP_NAME = 'k8sops'

def load_configs(config_dir):

    if os.path.isdir(config_dir):

        main_config_path = os.path.join(config_dir, 'config.yaml')
        mcp_config_path = os.path.join(config_dir, 'mcp_config.json')

        with open(main_config_path, "r") as f:
            main_config = yaml.safe_load(f)

        with open(mcp_config_path, "r") as f:
            mcp_config = json.load(f)

    else:

        main_config = {
            'model_config': {}
        }
        mcp_config = {
            'mcp_servers': {}
        }

    config = {
        "main_config": main_config,
        'mcp_servers': mcp_config['mcp_servers']
    }
    return config


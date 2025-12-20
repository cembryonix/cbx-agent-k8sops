# models/supported_models

SUPPORTED_MODELS = {
    "global_config": {
        "temperature": 0.1,
        "max_tokens": 2000,
        "timeout": 30,
        "max_retries": 3
    },
    "providers": {

        "openai": {
            "base_config": {
                "api_key_env": "OPENAI_API_KEY",
                "base_url": None,
                "organization": None
            },
            "models": {

                ##### GPT-4+
                "gpt-4o-mini": {
                    "display_name": "GPT-4o Mini",
                    "capabilities": ["chat", "tool_calling", "vision"],
                    "context_window": 128000,
                    "config_overrides": {}
                },
                "gpt-4o": {
                    "display_name": "GPT-4o",
                    "capabilities": ["chat", "tool_calling", "vision"],
                    "context_window": 128000,
                    "config_overrides": {"temperature": 0.1}
                }
            }
        },
        "ollama": {
            "base_config": {
                "base_url": "http://localhost:11434"
            },
            "models": {}
        },
        "anthropic": {
            "base_config": {
                "api_key_env": "ANTHROPIC_API_KEY"
            },
            "models": {}
        }


    }
}

# TODO: add selective return for only "enabled" models , i.e. "tested" models
def get_supported_models_data():
    """Returns only tested and supported models"""
    return SUPPORTED_MODELS

def get_supported_model_ids():

    models = get_supported_models_data()

    model_ids = {}

    for provider, provider_data in models["providers"].items():
        model_names = list(provider_data.get("models", {}).keys())
        model_ids[provider] = model_names


    available_models = model_ids

    return available_models

def get_provider_config(provider, model_name):

    models = get_supported_models_data()

    provider_data = models["providers"][provider]
    model_data = provider_data["models"][model_name]

    config = {}
    # add global
    config.update(models["global_config"])
    # add provider base
    config.update(provider_data["base_config"])
    # add model overrides
    config.update(model_data.get("config_overrides", {}))

    return config


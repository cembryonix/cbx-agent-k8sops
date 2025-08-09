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
                "gpt-4.1-nano": {
                    "display_name": "GPT-4.1 Nano",
                    "capabilities": ["chat", "tool_calling"],
                    "context_window": 1000000,
                    "config_overrides": {}
                },
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
                },
                ##### GPT-5+
                "gpt-5-nano": {
                    "display_name": "GPT-5 Nano",
                    "capabilities": ["chat", "tool_calling", "vision", "structured_output", "parallel_tools", "reasoning_params"],
                    "context_window": 272_000,
                    "config_overrides": {
                        "reasoning_effort": "minimal",
                        "verbosity": "low",
                    }
                },
                "gpt-5-mini": {
                    "display_name": "GPT-5 Mini",
                    "capabilities": ["chat", "tool_calling", "vision", "structured_output", "parallel_tools", "reasoning_params"],
                    # If you need an explicit number, treat this as the same tier unless your usage depends on exact limits.
                    "context_window": 272_000,
                    "config_overrides": {
                        "streaming": False,  # disabled until - TODO: add config flag for Organization verification status
                        "reasoning_effort": "minimal",
                        "verbosity": "low",
                    }
                },
                "gpt-5": {
                    "display_name": "GPT-5",
                    "capabilities": ["chat", "tool_calling", "vision", "structured_output", "parallel_tools", "reasoning_params"],
                    # Context window per official docs / Azure table; max output typically listed separately.
                    "context_window": 272_000,
                    "config_overrides": {
                        "streaming": False,  # TODO: add config flag for Organization verification status
                        # Available knobs (use as needed):
                        "reasoning_effort": "minimal",  # or "medium"/"high"
                        "verbosity": "low",             # or "medium"/"high"
                    }
                },
                "gpt-5-chat-latest": {
                    "display_name": "GPT-5 Chat (non-reasoning router)",
                    "capabilities": ["chat", "tool_calling", "vision", "structured_output", "parallel_tools"],
                    "context_window": 400_000,
                    "config_overrides": {
                        "streaming": False, # TODO: add config flag for Organization verification status
                        "verbosity": "low",
                    }
                }
            }
        },
        "ollama": {
            "base_config": {
                "base_url": "http://localhost:11434"
            },
            "models": {
                "llama3.2": {
                    "display_name": "Llama 3.2",
                    "capabilities": ["chat"],
                    "context_window": 4096,
                    "config_overrides": {
                      "temperature": 0.8
                    }
                }
            }
        },
        "anthropic": {
            "base_config": {
                "api_key_env": "ANTHROPIC_API_KEY"
            },
            "models": {
                "claude-3-5-sonnet-20241022": {
                    "display_name": "Claude 3.5 Sonnet",
                    "capabilities": ["chat", "tool_calling", "vision"],
                    "context_window": 200000,
                    "config_overrides": {
                        "max_tokens": 4096
                    }
                }
            }
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


"""
Configuration loader with YAML support.

Loads configuration from:
1. Built-in defaults: k8sops/config/defaults/
2. Environment variables (highest priority)
"""

import sys
from pathlib import Path
from typing import Any

import yaml

# Package defaults directory
DEFAULTS_DIR = Path(__file__).parent / "defaults"

# Cache for loaded configs
_models_config: dict[str, Any] | None = None
_settings_config: dict[str, Any] | None = None


def _load_yaml_file(path: Path) -> dict[str, Any]:
    """Load a YAML file, returning empty dict if not found."""
    if not path.exists():
        return {}
    try:
        with open(path) as f:
            content = yaml.safe_load(f)
            return content if content else {}
    except yaml.YAMLError as e:
        print(f"Warning: Failed to parse {path}: {e}", file=sys.stderr)
        return {}


def get_models_config() -> dict[str, Any]:
    """
    Get LLM provider/model configuration.

    Returns:
        Dict with 'providers', 'default_provider' keys
    """
    global _models_config
    if _models_config is None:
        _models_config = _load_yaml_file(DEFAULTS_DIR / "models.yaml")
    return _models_config


def get_settings_config() -> dict[str, Any]:
    """
    Get application settings configuration.

    Returns:
        Dict with 'llm', 'mcp', 'ui', 'app' keys
    """
    global _settings_config
    if _settings_config is None:
        _settings_config = _load_yaml_file(DEFAULTS_DIR / "settings.yaml")
    return _settings_config


def get_providers() -> list[str]:
    """Get list of available provider IDs."""
    config = get_models_config()
    return list(config.get("providers", {}).keys())


def get_provider_display_name(provider_id: str) -> str:
    """Get display name for a provider."""
    config = get_models_config()
    provider = config.get("providers", {}).get(provider_id, {})
    return provider.get("name", provider_id)


def get_default_provider() -> str:
    """Get the default provider ID."""
    config = get_models_config()
    return config.get("default_provider", "anthropic")


def get_models_for_provider(provider_id: str) -> list[dict[str, str]]:
    """
    Get available models for a provider.

    Returns:
        List of model dicts with 'id', 'name', 'description' keys
    """
    config = get_models_config()
    provider = config.get("providers", {}).get(provider_id, {})
    return provider.get("models", [])


def get_model_ids_for_provider(provider_id: str) -> list[str]:
    """Get just the model IDs for a provider."""
    models = get_models_for_provider(provider_id)
    return [m["id"] for m in models]


def get_default_model(provider_id: str) -> str:
    """Get the default model for a provider."""
    config = get_models_config()
    provider = config.get("providers", {}).get(provider_id, {})
    return provider.get("default_model", "")


def reload_config() -> None:
    """Force reload of configuration (for testing or hot-reload)."""
    global _models_config, _settings_config
    _models_config = None
    _settings_config = None

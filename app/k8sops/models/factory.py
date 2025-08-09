# models/factory.py

from typing import Dict, List, Any


from .supported_models import get_supported_model_ids
from .openai_client import (
    create_openai_model
)

from ..utils import get_logger
logger = get_logger(__name__)


async def initialize_model(provider: str, model_name: str, model_config: Dict[str, Any]):

    try:
        model = None
        logger.info(f"Initializing \"{provider}\" model: \"{model_name}\" ")
        # Validate model availability
        if not _is_model_available(provider, model_name):
            raise ValueError(f"Model {model_name} not available for provider {provider}")
        # Create model based on provider - each function extracts what it needs from CONFIG
        if provider == "openai":
            model = await _create_openai_model(model_name, model_config)
        elif provider == "anthropic":
            #model = await _create_anthropic_model(model_name, CONFIG)
            pass
        elif provider == "ollama":
            #model = await _create_ollama_model(model_name, CONFIG)
            pass

        # Validate model is working
        await _validate_model(model)

        logger.info(f"Successfully initialized {provider} model: {model_name}")
        return model

    except Exception as e:
        logger.error(f"Failed to initialize model {model_name} for {provider}: {e}")
        # can not do anything without model
        raise

############################################################################

async def _create_openai_model(model_name: str, model_config: Dict[str, Any]):

    # Update or set defaults OpenAI-specific parameters from model_config
    openai_params = {
        # Common parameters
        'temperature': model_config.get('temperature', 0.7),
        'max_tokens': model_config.get('max_tokens', 2000),
        'streaming': model_config.get('streaming', True),

        # OpenAI-specific parameters
        'top_p': model_config.get('openai', {}).get('top_p', 1.0),
        'frequency_penalty': model_config.get('openai', {}).get('frequency_penalty', 0.0),
        'presence_penalty': model_config.get('openai', {}).get('presence_penalty', 0.0),
        'timeout': model_config.get('openai', {}).get('timeout', 30),
        'max_retries': model_config.get('openai', {}).get('max_retries', 3),
    }

    # Remove None values
    openai_params = {k: v for k, v in openai_params.items() if v is not None}

    logger.debug(f"OpenAI params: {openai_params}")
    model = create_openai_model(model_name, **openai_params)
    return model


################################
async def _validate_model(model):

    try:
        # Simple test to ensure model responds
        test_response = await model.ainvoke("test")
        if not test_response:
            raise ConnectionError("Model validation failed - no response")
    except Exception as e:
        raise ConnectionError(f"Model validation failed: {e}")


def _is_model_available(provider: str, model_name: str) -> bool:

    available_models = get_supported_model_ids()
    return model_name in available_models.get(provider, [])
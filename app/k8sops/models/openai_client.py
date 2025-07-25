
import os
from typing import Dict, Any

from langchain_openai import ChatOpenAI

from ..utils import get_logger
logger = get_logger(__name__)

from .supported_models import get_supported_model_ids

# # OpenAI-specific model list
# VALID_OPENAI_MODELS = [
#     'gpt-4.1-nano', 'gpt-4.1-mini', 'gpt-3.5-turbo', 'gpt-4-turbo'
# ]

def create_openai_model(model_name: str, **kwargs) -> ChatOpenAI:

    logger.debug(f"Creating OpenAI model: {model_name}")

    valid_models = get_supported_model_ids().get('openai', [])

    # Validate model name
    if model_name not in valid_models:
        logger.warning(f"Model {model_name} not in known valid models  : {valid_models}")

    # Check API key
    api_key = kwargs.get('api_key') or os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable or pass api_key parameter")

    # Process OpenAI-specific parameters
    openai_kwargs = _prepare_openai_kwargs(kwargs)

    try:
        model = ChatOpenAI(
            model=model_name,
            **openai_kwargs
        )
        logger.debug(f"Successfully created OpenAI model: {model_name}")
        return model

    except Exception as e:
        logger.error(f"Failed to create OpenAI model {model_name}: {e}")
        raise


def _prepare_openai_kwargs(kwargs: Dict[str, Any]) -> Dict[str, Any]:

    # Set OpenAI-specific defaults
    openai_kwargs = {
        'temperature': kwargs.get('temperature', 0.7),
        'streaming': kwargs.get('streaming', True),
        'request_timeout': kwargs.get('request_timeout', 30),
        'max_retries': kwargs.get('max_retries', 3),
    }

    # Add any other provided kwargs that are valid for ChatOpenAI
    valid_openai_params = [
        'max_tokens', 'top_p', 'frequency_penalty', 'presence_penalty',
        'api_key', 'base_url', 'organization'
    ]

    for param in valid_openai_params:
        if param in kwargs:
            openai_kwargs[param] = kwargs[param]

    return openai_kwargs



def validate_openai_config(config: Dict[str, Any]) -> bool:

    # Check temperature range
    temp = config.get('temperature', 0.7)
    if not 0 <= temp <= 2:
        logger.warning(f"Temperature {temp} outside recommended range [0, 2]")
        return False

    # Check max_tokens if provided
    max_tokens = config.get('max_tokens')
    if max_tokens and (max_tokens < 1 or max_tokens > 4096):
        logger.warning(f"max_tokens {max_tokens} may be outside valid range")
        return False

    return True
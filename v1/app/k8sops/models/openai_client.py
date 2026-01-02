# models/openai_client.py

import os
from typing import Dict, Any

from langchain_openai import ChatOpenAI

from .supported_models import get_supported_model_ids
from ..utils import get_logger
logger = get_logger(__name__)



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
    openai_kwargs = _prepare_openai_kwargs(model_name, kwargs)

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


def _prepare_openai_kwargs(model_name: str, kwargs: Dict[str, Any]) -> Dict[str, Any]:

    # Determine if this is a GPT-5 model
    is_gpt5_model = model_name.startswith('gpt-5')

    # GPT-5 models only support temperature = 1.0 (default)
    if is_gpt5_model and 'temperature' in kwargs and kwargs['temperature'] != 1.0:
        logger.warning(f"GPT-5 model {model_name} only supports temperature=1.0, removing temperature parameter")
        kwargs = kwargs.copy()  # Don't modify original
        kwargs.pop('temperature', None)

    # Set OpenAI-specific defaults
    openai_kwargs = {
        'streaming': kwargs.get('streaming', True),
        'request_timeout': kwargs.get('request_timeout', 30),
        'max_retries': kwargs.get('max_retries', 3),
    }

    # Add temperature only for non-GPT-5 models
    if not is_gpt5_model:
        openai_kwargs['temperature'] = kwargs.get('temperature', 0.7)

    # Standard OpenAI parameters
    valid_openai_params = [
        'max_tokens', 'top_p', 'frequency_penalty', 'presence_penalty',
        'api_key', 'base_url', 'organization'
    ]

    # GPT-5 specific parameters
    gpt5_params = ['reasoning_effort', 'verbosity']

    # Add standard parameters
    for param in valid_openai_params:
        if param in kwargs:
            openai_kwargs[param] = kwargs[param]

    # Add GPT-5 parameters only for GPT-5 models
    if is_gpt5_model:
        for param in gpt5_params:
            if param in kwargs:
                openai_kwargs[param] = kwargs[param]
                logger.debug(f"Adding GPT-5 parameter {param}: {kwargs[param]}")

    logger.debug(f"Final OpenAI kwargs for {model_name}: {openai_kwargs}")
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

    # Validate GPT-5 specific parameters
    reasoning_effort = config.get('reasoning_effort')
    if reasoning_effort and reasoning_effort not in ['minimal', 'low', 'medium', 'high']:
        logger.warning(f"Invalid reasoning_effort: {reasoning_effort}")
        return False

    verbosity = config.get('verbosity')
    if verbosity and verbosity not in ['low', 'medium', 'high']:
        logger.warning(f"Invalid verbosity: {verbosity}")
        return False

    return True
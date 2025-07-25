
import chainlit as cl
from chainlit.input_widget import Select, Slider

from ..models import get_supported_model_ids

from ..utils import get_logger
logger = get_logger(__name__)

async def create_chat_settings(default_configs) -> cl.ChatSettings:

    model_list = []
    for provider, models in get_supported_model_ids().items():
        for model in models:
            model_list.append(f"{provider}/{model}")

    settings = await cl.ChatSettings([
        Select(
            id="model",
            label="AI Model",
            values=model_list,
            initial_index=0,
        ),
        Slider(
            id="temperature",
            label="Temperature",
            initial=0.1,
            min=0,
            max=1,
            step=0.1,
            tooltip="Controls randomness in responses",
        )
    ]).send()

    return settings
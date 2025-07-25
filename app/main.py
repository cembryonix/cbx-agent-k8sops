
import chainlit as cl
import os

from k8sops.utils import setup_logging, get_logger
from k8sops.config import load_configs

from k8sops.chainlit_handlers import init_session
from k8sops.chainlit_handlers import handle_message
from k8sops.chainlit_handlers import handle_settings_update
from k8sops.chainlit_handlers import cleanup_session


setup_logging(level='INFO')
logger = get_logger(__name__)

# Get K8SOps config dir
default_config_dir = os.environ.get('K8SOPS_CONFIG_DIR', os.path.expanduser(f"~/.k8sops"))
logger.debug(default_config_dir)

# Load Configs and pass it as needed
# "CONFIG" - static and used as default for "settings"
# "settings" - can be changed interactively
default_config = load_configs(default_config_dir)
logger.debug(default_config)


@cl.on_chat_start
async def on_chat_start():
    await init_session(default_config)

@cl.on_settings_update
async def on_settings_update(settings):
    """Handle settings updates - delegates to settings handler"""
    await handle_settings_update(settings, default_config)

@cl.on_chat_end
async def on_chat_end():
    await cleanup_session()

@cl.on_message
async def on_message(message: cl.Message):
    await handle_message(message)






if __name__ == "__main__":

    cl.run()
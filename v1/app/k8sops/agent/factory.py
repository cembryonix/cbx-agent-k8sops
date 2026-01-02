# agent/factory.py

from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from .prompts import get_system_prompt

async def setup_agent(model,tools):

    memory = MemorySaver()
    model_name = model.model_name
    system_prompt = get_system_prompt(model_name)

    agent = create_react_agent(
        model = model,
        tools = tools,
        checkpointer = memory,
        prompt = system_prompt
    )

    return agent



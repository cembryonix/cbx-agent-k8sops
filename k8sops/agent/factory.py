"""Agent factory for creating LangGraph agents."""

import logging
from typing import Any

from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool

from .prompts import get_system_prompt, format_tool_descriptions

logger = logging.getLogger(__name__)


def create_agent(
    model: BaseChatModel,
    tools: list[BaseTool],
    checkpointer: Any | None = None,
    memory_context: str = "",
) -> Any:
    """Create a LangGraph ReAct agent.

    Args:
        model: LangChain chat model
        tools: List of LangChain tools
        checkpointer: Optional checkpointer for conversation memory
        memory_context: Optional context from long-term memory

    Returns:
        LangGraph agent instance
    """
    # Build system message for the agent
    tool_defs = [
        {"name": t.name, "description": t.description}
        for t in tools
    ]
    tool_descriptions = format_tool_descriptions(tool_defs)
    system_prompt = get_system_prompt(tool_descriptions, memory_context)

    # Use memory saver if no checkpointer provided
    if checkpointer is None:
        checkpointer = MemorySaver()

    logger.info(f"Creating agent with {len(tools)} tools")

    # create_react_agent handles tool binding internally
    agent = create_react_agent(
        model=model,
        tools=tools,
        checkpointer=checkpointer,
        prompt=system_prompt,
    )

    return agent


async def create_agent_with_mcp(
    model: BaseChatModel,
    mcp_client: Any,
    checkpointer: Any | None = None,
    memory_context: str = "",
) -> Any:
    """Create agent with tools from MCP client.

    Args:
        model: LangChain chat model
        mcp_client: Connected MCPClient instance
        checkpointer: Optional checkpointer for conversation memory
        memory_context: Optional context from long-term memory

    Returns:
        LangGraph agent instance
    """
    tools = mcp_client.get_langchain_tools()
    return create_agent(model, tools, checkpointer, memory_context)

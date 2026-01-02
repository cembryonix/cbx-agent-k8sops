#!/usr/bin/env python3
"""Debug script to test agent tool binding."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

async def main():
    from k8sops.mcp_client import MCPClient
    from k8sops.models import create_model
    from langgraph.prebuilt import create_react_agent
    from langgraph.checkpoint.memory import MemorySaver

    print("1. Connecting to MCP server...")
    client = MCPClient(ssl_verify=False)
    tools = await client.connect()
    print(f"   Found {len(tools)} tools")

    print("\n2. Getting LangChain tools...")
    lc_tools = client.get_langchain_tools()
    for t in lc_tools:
        print(f"   - {t.name}: {type(t).__name__}")
        print(f"     Description: {t.description[:80] if t.description else 'None'}...")

    print("\n3. Creating model...")
    model = create_model()
    print(f"   Model: {type(model).__name__}")

    print("\n4. Testing tool binding on model...")
    model_with_tools = model.bind_tools(lc_tools)
    print(f"   Model with tools: {type(model_with_tools).__name__}")

    print("\n5. Testing direct model call with tools...")
    from langchain_core.messages import HumanMessage
    response = await model_with_tools.ainvoke([
        HumanMessage(content="List namespaces in the cluster. Use the available tools.")
    ])
    print(f"   Response type: {type(response).__name__}")
    print(f"   Has tool_calls: {bool(response.tool_calls)}")
    if response.tool_calls:
        for tc in response.tool_calls:
            print(f"   Tool call: {tc['name']} with args {tc['args']}")
    else:
        print(f"   Content: {response.content[:200]}...")

    print("\n6. Creating ReAct agent WITH custom prompt...")
    from k8sops.agent.prompts import get_system_prompt, format_tool_descriptions
    tool_defs = [{"name": t.name, "description": t.description or ""} for t in lc_tools]
    tool_desc = format_tool_descriptions(tool_defs)
    system_prompt = get_system_prompt(tool_desc)
    print(f"   System prompt length: {len(system_prompt)} chars")

    agent = create_react_agent(
        model=model,
        tools=lc_tools,
        checkpointer=MemorySaver(),
        prompt=system_prompt,
    )
    print(f"   Agent created: {type(agent).__name__}")

    print("\n7. Testing agent invocation...")
    config = {"configurable": {"thread_id": "test"}}
    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "List all namespaces"}]},
        config=config,
    )

    print(f"   Messages count: {len(result['messages'])}")
    for i, msg in enumerate(result['messages']):
        msg_type = type(msg).__name__
        has_tc = hasattr(msg, 'tool_calls') and msg.tool_calls
        print(f"   [{i}] {msg_type}: has_tool_calls={has_tc}")

    # Check final message
    final = result['messages'][-1]
    print(f"\n   Final response: {final.content[:300]}...")

    await client.disconnect()
    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())

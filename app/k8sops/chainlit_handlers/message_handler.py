# chainlit_handlers/message_handler.py

# Main logic of the Interaction

import json
import chainlit as cl
from langchain_core.messages import AIMessage, HumanMessage

from ..utils import get_logger
logger = get_logger(__name__)

def format_tool_call(name, args):
    if not args:
        return f"**Tool:** `{name}`\n**Args:** _None_"
    if isinstance(args, dict):
        if 'command' in args:
            return f"**Tool:** `{name}`\n**Command:**\n```bash\n{args['command']}\n```"
        else:
            arg_lines = [f"{k}: {v}" for k, v in args.items()]
            return f"**Tool:** `{name}`\n**Args:**\n" + '\n'.join(arg_lines)
    return f"**Tool:** `{name}`\n**Args:** {args}"

def format_tool_output(output):
    return f"```text\n{output}\n```"


async def handle_message(message: cl.Message):
    agent = cl.user_session.get('agent')
    if agent is None:
        await cl.Message(content="❌ Agent not initialized. Please restart the chat.").send()
        return

    thread_id = cl.user_session.get('thread_id')
    config = {"configurable": {"thread_id": thread_id}}

    msg = cl.Message(content="")
    await msg.send()

    tool_calls = {}  # tool_call_id -> {'name': ..., 'args': ...}

    try:
        async for chunk in agent.astream({'messages': [HumanMessage(content=message.content)]}, config=config):
            # 1. Extract tool calls from agent node messages
            if 'agent' in chunk and 'messages' in chunk['agent']:
                for msg_obj in chunk['agent']['messages']:
                    if hasattr(msg_obj, 'tool_calls') and msg_obj.tool_calls:
                        for tool_call in msg_obj.tool_calls:
                            tool_call_id = tool_call['id']
                            name = tool_call['name']
                            args = tool_call.get('args', {})
                            logger.debug(f"Tool call: id={tool_call_id}, name={name}, args={args}")
                            tool_calls[tool_call_id] = {
                                'name': name,
                                'args': args
                            }
            # 2. Capture tool results and display with matching command
            if 'tools' in chunk and 'messages' in chunk['tools']:
                for tool_msg in chunk['tools']['messages']:
                    tool_call_id = getattr(tool_msg, 'tool_call_id', None)
                    content = getattr(tool_msg, 'content', None)
                    if tool_call_id and content:
                        call = tool_calls.get(tool_call_id)
                        if call:
                            call_md = format_tool_call(call['name'], call['args'])
                            try:
                                result_json = json.loads(content)
                                output = result_json.get('output', content)
                            except Exception:
                                output = content
                            output_md = format_tool_output(output)
                            # Display as a collapsible step
                            command = call['args'].get('command', '')
                            async with cl.Step(name=call['name'], type="tool") as step:
                                step.input = f"```bash\n{command}\n```"
                                step.output = output_md
                        else:
                            await cl.Message(content=f"Tool output (raw):\n{content}").send()
            # 3. Stream normal LLM output
            if 'agent' in chunk and 'messages' in chunk['agent']:
                for msg_obj in chunk['agent']['messages']:
                    if hasattr(msg_obj, 'content') and msg_obj.content:
                        await msg.stream_token(msg_obj.content)
    except Exception as e:
        await msg.stream_token(f"❌ Error: {str(e)}")

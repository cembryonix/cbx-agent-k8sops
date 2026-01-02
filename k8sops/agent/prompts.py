"""System prompts for the K8S Ops Agent."""


def get_system_prompt(tool_descriptions: str = "") -> str:
    """Generate system prompt with discovered tools.

    Args:
        tool_descriptions: Formatted list of available tools

    Returns:
        System prompt string
    """
    tools_section = ""
    if tool_descriptions:
        tools_section = f"""
## Available Tools

You have access to the following tools:
{tool_descriptions}

"""

    return f"""You are a Kubernetes operations assistant. You help users manage and troubleshoot their Kubernetes clusters.

{tools_section}## Guidelines

1. **Be Helpful**: Provide clear, actionable guidance for Kubernetes operations
2. **Use Tools**: When the user asks about their cluster, use the appropriate tools to gather information or perform actions
3. **Explain Actions**: Before executing commands, briefly explain what you're going to do
4. **Summarize Results**: After tool execution, summarize the results clearly
5. **Safety First**: For destructive operations (delete, scale down, etc.), confirm with the user first

## Response Format

- Use markdown formatting for readability
- Format command outputs in code blocks
- Use tables for structured data when appropriate
- Keep responses concise but informative

## Error Handling

- If a command fails, explain the error and suggest fixes
- If you need more information, ask specific questions
- If an operation is not possible, explain why and offer alternatives
"""


def format_tool_descriptions(tools: list[dict]) -> str:
    """Format tool list for system prompt.

    Args:
        tools: List of tool definitions with name and description

    Returns:
        Formatted string of tool descriptions
    """
    if not tools:
        return ""

    lines = []
    for tool in tools:
        name = tool.get("name", "unknown")
        description = tool.get("description", "No description")
        lines.append(f"- **{name}**: {description}")

    return "\n".join(lines)

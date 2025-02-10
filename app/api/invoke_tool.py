import asyncio
from app.api.tool_registry import get_tool_handler

async def invoke_tool(tool_call: dict):
    """
    Invoke a tool based on the provided tool_call data.
    Expected tool_call structure: 
      {
        "tool": "<tool_name>",
        "parameters": { ... }
      }
    """
    tool_name = tool_call.get("tool")
    parameters = tool_call.get("parameters", {})
    handler = get_tool_handler(tool_name)
    if not handler:
        return {"error": f"No handler registered for tool {tool_name}"}
    try:
        return await handler(**parameters)
    except Exception as e:
        return {"error": str(e)}
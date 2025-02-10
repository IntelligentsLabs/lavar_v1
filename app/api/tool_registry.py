tool_handlers = {}

def register_tool_handler(name):
    """
    Decorator to register a tool handler function.
    The decorated function will be stored in the tool_handlers dictionary.
    """
    def decorator(func):
        tool_handlers[name] = func
        return func
    return decorator

def get_tool_handler(name):
    """Retrieve a registered tool handler by name."""
    return tool_handlers.get(name)

def list_registered_tools():
    """List all registered tool handler names."""
    return list(tool_handlers.keys())
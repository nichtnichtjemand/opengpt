from mcp.server.mcpserver import MCPServer

mcp = MCPServer("OpenGPT-Tools")


@mcp.tool()
def secret() -> str:
    """Returns the secret word"""
    return "Apple"


@mcp.tool()
def system_status() -> str:
    """Returns current MCP connection status"""
    return "Everything seems to work here!"


@mcp.tool()
def get_weather(city: str) -> str:
    """Returns the current weather for a given city"""

    return f"The current weather in {city} is sunny with a temperature of 25°C."


if __name__ == "__main__":
    mcp.run()

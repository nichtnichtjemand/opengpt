import requests
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
    url = f"https://wttr.in/{city}"
    query_params = {"format": "4", "m": ""}

    response = requests.get(url, params=query_params)
    return response.text


if __name__ == "__main__":
    mcp.run()

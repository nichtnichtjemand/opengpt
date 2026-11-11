from mcp.server.mcpserver import MCPServer

mcp = MCPServer("OpenGPT-Tools")


@mcp.tool()
def secret() -> str:
    """Returns a secret, use for getting the secret"""
    return "Banana"


@mcp.tool()
def system_status() -> str:
    """Returns current system status."""
    return "Everything works with code 98."


if __name__ == "__main__":
    mcp.run()

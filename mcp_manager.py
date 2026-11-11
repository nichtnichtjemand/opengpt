import os
import sys
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPManager:
    def __init__(self, server_script: str):
        self.server_params = StdioServerParameters(
            command=sys.executable,
            args=["-u", server_script],
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )
        self.exit_stack = AsyncExitStack()
        self.session: ClientSession | None = None
        self.gemini_tools: list[dict] = []

    async def connect(self):
        read, write = await self.exit_stack.enter_async_context(
            stdio_client(self.server_params)
        )
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(read, write, read_timeout_seconds=5.0)
        )
        await self.session.initialize()

        mcp_tools = await self.session.list_tools()
        self.gemini_tools = [
            {
                "type": "function",
                "name": tool.name,
                "description": tool.description or "",
                "parameters": tool.input_schema,
            }
            for tool in mcp_tools.tools
        ]

    async def execute_tool(self, name: str, arguments: dict) -> str:
        if not self.session:
            raise RuntimeError("MCP-Session is not connected.")

        result = await self.session.call_tool(name=name, arguments=arguments)
        return result.content[0].text if result.content else ""

    async def close(self):
        await self.exit_stack.aclose()

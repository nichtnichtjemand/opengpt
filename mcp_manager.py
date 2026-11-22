import os
import sys
from contextlib import AsyncExitStack
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPManager:
    def __init__(self, server_script: str):
        script_path = Path(server_script)
        frozen = bool(getattr(sys, "frozen", False))

        if frozen and not script_path.is_absolute():
            candidates = [
                Path(getattr(sys, "_MEIPASS", "")),
                Path(__file__).resolve().parent,
                Path.cwd(),
            ]
            script_path = next(
                (
                    candidate / server_script
                    for candidate in candidates
                    if candidate and (candidate / server_script).is_file()
                ),
                script_path,
            )

        self.server_params = StdioServerParameters(
            command=sys.executable,
            args=["--mcp-server"] if frozen else ["-u", str(script_path)],
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )
        self.exit_stack = AsyncExitStack()
        self.session: ClientSession | None = None
        self.gemini_tools: list[dict] = []
        self.openai_tools: list[dict] = []  # <-- NEU

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

        self.openai_tools = [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.input_schema,
                },
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

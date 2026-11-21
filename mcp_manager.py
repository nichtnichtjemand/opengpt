import os
import sys
import importlib.util
from pathlib import Path
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPManager:
    def __init__(self, server_script: str):
        script_path = Path(server_script)
        executable_name = Path(sys.executable).name.lower()
        bundle_mode = (
            bool(getattr(sys, "_MEIPASS", None))
            or bool(getattr(sys, "frozen", False))
            or executable_name in {"opengpt", "opengpt.exe"}
            or "__mamp" in executable_name
        )
        if not script_path.is_absolute():
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
        server_args = (
            ["--mcp-server"]
            if bundle_mode
            else ["-u", str(script_path)]
        )
        self.server_params = StdioServerParameters(
            command=sys.executable,
            args=server_args,
            env={
                **os.environ,
                "PYTHONUNBUFFERED": "1",
                "OPENGPT_MCP_SERVER": "1",
            },
        )
        self.exit_stack = AsyncExitStack()
        self.session: ClientSession | None = None
        self.gemini_tools: list[dict] = []
        self.openai_tools: list[dict] = []
        self.bundle_mode = bundle_mode
        self.direct_server = None

    async def connect(self):
        if self.bundle_mode:
            mcp_root = next(
                (
                    candidate / "resources" / "mcp"
                    for candidate in (
                        Path(getattr(sys, "_MEIPASS", "")),
                        Path(__file__).resolve().parent,
                        Path.cwd(),
                    )
                    if candidate
                    and (candidate / "resources" / "mcp").is_dir()
                ),
                Path("resources/mcp"),
            )
            sys.path.insert(0, str(mcp_root))
            server_py = mcp_root / "main_server.py"
            server_pyc = mcp_root / "main_server.pyc"
            server_file = server_py if server_py.is_file() else server_pyc
            spec = importlib.util.spec_from_file_location("opengpt_mcp_server", server_file)
            if spec is None or spec.loader is None:
                raise RuntimeError(f"Cannot load MCP server: {server_file}")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.direct_server = module.mcp

            mcp_tools = await self.direct_server.list_tools()
            self.gemini_tools = [
                {
                    "type": "function",
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.input_schema,
                }
                for tool in mcp_tools
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
                for tool in mcp_tools
            ]
            return

        read, write = await self.exit_stack.enter_async_context(
            stdio_client(self.server_params)
        )
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(read, write, read_timeout_seconds=30.0)
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
        if self.direct_server is not None:
            result = await self.direct_server.call_tool(name, arguments)
            if getattr(result, "structuredContent", None):
                import json
                return json.dumps(result.structuredContent)
            if getattr(result, "content", None):
                return "\n".join(
                    getattr(item, "text", str(item))
                    for item in result.content
                )
            return ""

        if not self.session:
            raise RuntimeError("MCP-Session is not connected.")

        result = await self.session.call_tool(name=name, arguments=arguments)
        return result.content[0].text if result.content else ""

    async def close(self):
        await self.exit_stack.aclose()

import asyncio
import runpy
import sys
from pathlib import Path

import terminal


def resource_root() -> Path:
    candidates = [
        Path(getattr(sys, "_MEIPASS", "")),
        Path(__file__).resolve().parent,
        Path.cwd(),
    ]
    for candidate in candidates:
        if candidate and (candidate / "resources").is_dir():
            return candidate
    return Path(__file__).resolve().parent


def run_mcp_server() -> None:
    mcp_root = resource_root() / "resources" / "mcp"
    sys.path.insert(0, str(mcp_root))
    runpy.run_path(
        str(mcp_root / "main_server.py"),
        run_name="__main__",
    )


async def main():
    await terminal.main()


if __name__ == "__main__":
    if "--mcp-server" in sys.argv:
        run_mcp_server()
    else:
        asyncio.run(main())

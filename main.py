import asyncio
import logging
import runpy
import sys
from pathlib import Path

import terminal

logger = logging.getLogger("opengpt")
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

formatter = logging.Formatter(
    fmt="%(asctime)s [%(levelname).4s] %(module)s: %(message)s", datefmt="%H:%M:%S"
)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

logger.debug("Starting OpenGPT...")


def run_mcp_server():
    bundle_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    mcp_root = bundle_root / "resources" / "mcp"
    sys.path.insert(0, str(mcp_root))
    runpy.run_path(str(mcp_root / "main_server.py"), run_name="__main__")


async def main():
    await terminal.main()


if __name__ == "__main__":
    if "--mcp-server" in sys.argv:
        run_mcp_server()
    else:
        asyncio.run(main())

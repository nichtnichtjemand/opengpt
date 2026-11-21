import asyncio
import io
import logging
import os
import runpy
import sys
from pathlib import Path

import app

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
    for stream_name, fd in (("stdin", 0), ("stdout", 1), ("stderr", 2)):
        stream = getattr(sys, stream_name)
        if not hasattr(stream, "buffer"):
            mode = "rb" if stream_name == "stdin" else "wb"
            binary = os.fdopen(fd, mode, buffering=0, closefd=False)
            text = io.TextIOWrapper(binary, encoding="utf-8", write_through=True)
            setattr(sys, stream_name, text)

    candidates = [
        Path(getattr(sys, "_MEIPASS", "")),
        Path(__file__).resolve().parent,
        Path.cwd(),
    ]
    bundle_root = next(
        (candidate for candidate in candidates if candidate and (candidate / "resources").is_dir()),
        Path(__file__).resolve().parent,
    )
    mcp_root = bundle_root / "resources" / "mcp"
    sys.path.insert(0, str(mcp_root))
    server_py = mcp_root / "main_server.py"
    server_pyc = mcp_root / "main_server.pyc"
    runpy.run_path(
        str(server_py if server_py.is_file() else server_pyc),
        run_name="__main__",
    )


async def main():
    await app.run()


if __name__ == "__main__":
    if "--mcp-server" in sys.argv or os.getenv("OPENGPT_MCP_SERVER") == "1":
        run_mcp_server()
    else:
        asyncio.run(main())

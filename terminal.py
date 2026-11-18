import asyncio
import logging

from rich.console import Console
from rich.markdown import Markdown

import aiapi
import mcp_manager

logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger("opengpt." + __name__)

console = Console()


def ui_tool_status(tool_name: str, args: dict):
    logger.debug(f"[MCP-Tool] Execute '{tool_name}' (Parameter: {args})...")


async def main():
    logger.debug("Connect to MCP Server...")
    mcp = mcp_manager.MCPManager("resources/mcp/main_server.py")
    await mcp.connect()
    running = True

    try:
        logger.info("Started OpenGPT")
        conversation = aiapi.Conversation(
            mcp=mcp,  # provider="groq", model="openai/gpt-oss-120b"
        )

        while running:
            user_input = await asyncio.to_thread(input, "\nYou: ")

            if user_input.startswith("!"):
                logger.debug("Command detected")

                command = user_input[1:].split(" ")
                start_command = command[0]
                arguments = command[1:]

                match start_command:
                    case "exit":
                        running = False
                    case "quit":
                        running = False
                    case "model":
                        conversation.model = arguments[0]

            else:
                reply = await conversation.send_message(
                    message=user_input, on_tool_call=ui_tool_status
                )
                console.print(Markdown(reply))

    finally:
        await mcp.close()


if __name__ == "__main__":
    asyncio.run(main())

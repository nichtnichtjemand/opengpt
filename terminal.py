import asyncio
import logging

import aiapi
import mcp_manager

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger("opengpt")


def ui_tool_status(tool_name: str, args: dict):
    logger.debug(f"[MCP-Tool] Execute '{tool_name}' (Parameter: {args})...")


async def main():

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.debug("Connect to MCP Server...")
    mcp = mcp_manager.MCPManager("resources/mcp/main_server.py")
    await mcp.connect()
    running = True

    try:
        logger.info("Started OpenGPT")
        conversation = aiapi.Conversation(
            mcp=mcp, provider="groq", model="openai/gpt-oss-120b"
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
                logger.info(f"\nOpenGPT:\n{reply}")

    finally:
        await mcp.close()


if __name__ == "__main__":
    asyncio.run(main())

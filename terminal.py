import asyncio

import googleapi
import mcp_manager

running = True


def ui_tool_status(tool_name: str, args: dict):
    print(f"⚙️ [MCP-Tool] Execute '{tool_name}' (Parameter: {args})...")


async def main():
    print("Connect to MCP Server...")
    mcp = mcp_manager.MCPManager("resources/mcp/main_server.py")
    await mcp.connect()

    try:
        print("Started OpenGPT! Type your questions here.")
        conversation = googleapi.Conversation(mcp=mcp)

        while running:
            user_input = await asyncio.to_thread(input, "\nYou: ")

            if user_input.strip().lower() in ["exit", "quit"]:
                break

            print("Running...")
            reply = await conversation.send_message(
                message=user_input, on_tool_call=ui_tool_status
            )
            print(f"\nOpenGPT:\n{reply}")

    finally:
        await mcp.close()


if __name__ == "__main__":
    asyncio.run(main())

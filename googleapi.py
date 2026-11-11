import os
from collections.abc import Callable

from dotenv import load_dotenv
from google import genai

from mcp_manager import MCPManager

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key, http_options={"timeout": 30000})


class Conversation:
    def __init__(self, mcp: MCPManager):
        self.conversation_id = None
        self.system_prompt = self.get_system_prompt()
        self.mcp = mcp

    async def send_message(
        self, message: str, on_tool_call: Callable[[str, dict], None] | None = None
    ) -> str | None:

        generation_config = {
            "max_output_tokens": 65536,
            "thinking_level": "minimal",
        }

        current_input = message

        try:
            while True:
                kwargs = {
                    "model": "gemini-3.5-flash-lite",
                    "input": current_input,
                    "generation_config": generation_config,
                    "system_instruction": self.system_prompt,
                    "tools": self.mcp.gemini_tools,
                }
                if self.conversation_id is not None:
                    kwargs["previous_interaction_id"] = self.conversation_id

                interaction = await client.aio.interactions.create(**kwargs)
                self.conversation_id = interaction.id

                # Geändert: interaction.steps statt interaction.outputs
                function_calls = [
                    step for step in interaction.steps if step.type == "function_call"
                ]

                if not function_calls:
                    return interaction.output_text or ""

                tool_results = []
                for call in function_calls:
                    if on_tool_call:
                        on_tool_call(call.name, call.arguments or {})

                    result_text = await self.mcp.execute_tool(
                        call.name, call.arguments or {}
                    )

                    tool_results.append(
                        {
                            "type": "function_result",
                            "call_id": call.id,
                            "name": call.name,
                            "result": result_text,
                        }
                    )

                current_input = tool_results

        except Exception as e:  # noqa: BLE001
            print("Error in interactions.create:", type(e).__name__, e)
            return None

    def get_system_prompt(self):
        with open("resources/prompts/systemprompt1.txt", "r", encoding="utf-8") as file:
            content = file.read()
        return content

import json
import os
import sys
from collections.abc import Callable
from pathlib import Path

from google import genai
from groq import AsyncGroq

from mcp_manager import MCPManager


def prompt_for_api_keys() -> dict[str, str]:
    """Prompt for API keys at runtime and expose them to local MCP processes."""
    keys = {
        "GOOGLE_API_KEY": input("Google API key: ").strip(),
        "GROQ_API_KEY": input("Groq API key: ").strip(),
        "TAVILY_API_KEY": input("Tavily API key: ").strip(),
    }
    missing = [name for name, value in keys.items() if not value]
    if missing:
        raise ValueError(
            "Missing required API key(s): " + ", ".join(missing)
        )
    os.environ.update(keys)
    return keys


class Conversation:
    def __init__(
        self,
        mcp: MCPManager,
        provider: str = "google",
        model: str = "gemini-3.5-flash-lite",
    ):
        self.system_prompt = self.get_system_prompt()
        self.mcp = mcp
        self.provider = provider.lower()
        self.model = model
        if self.provider == "google":
            self.google_client = genai.Client(
                api_key=os.environ["GOOGLE_API_KEY"],
                http_options={"timeout": 30000},
            )
        elif self.provider == "groq":
            self.groq_client = AsyncGroq(
                api_key=os.environ["GROQ_API_KEY"],
                timeout=30.0,
            )
        else:
            raise ValueError(f"Unbekannter Provider: {self.provider}")

        self.conversation_id = None

        self.messages: list[dict] = [{"role": "system", "content": self.system_prompt}]

    async def send_message(
        self, message: str, on_tool_call: Callable[[str, dict], None] | None = None
    ) -> str | None:
        if self.provider == "google":
            return await self._send_google(message, on_tool_call)
        elif self.provider == "groq":
            return await self._send_groq(message, on_tool_call)
        else:
            raise ValueError(f"Unbekannter Provider: {self.provider}")

    async def _send_google(
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
                    "model": self.model,
                    "input": current_input,
                    "generation_config": generation_config,
                    "system_instruction": self.system_prompt,
                    "tools": self.mcp.gemini_tools,
                }
                if self.conversation_id is not None:
                    kwargs["previous_interaction_id"] = self.conversation_id

                interaction = await self.google_client.aio.interactions.create(**kwargs)
                self.conversation_id = interaction.id

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
            print("Error in Google interactions.create:", type(e).__name__, e)
            return None

    async def _send_groq(
        self, message: str, on_tool_call: Callable[[str, dict], None] | None = None
    ) -> str | None:
        self.messages.append({"role": "user", "content": message})

        groq_tools = getattr(self.mcp, "openai_tools", None)

        try:
            while True:
                kwargs = {
                    "model": self.model,
                    "messages": self.messages,
                    "temperature": 1.0,
                    "max_completion_tokens": 4096,
                    "top_p": 1.0,
                    "stream": False,
                }

                if "gpt-oss" in self.model or "qwen3" in self.model:
                    kwargs["reasoning_effort"] = "medium"

                if groq_tools:
                    kwargs["tools"] = groq_tools

                completion = await self.groq_client.chat.completions.create(**kwargs)
                response_message = completion.choices[0].message

                assistant_msg: dict = {
                    "role": "assistant",
                    "content": response_message.content or "",
                }
                if response_message.tool_calls:
                    assistant_msg["tool_calls"] = [
                        tc.model_dump() for tc in response_message.tool_calls
                    ]
                self.messages.append(assistant_msg)

                if not response_message.tool_calls:
                    return response_message.content or ""

                for tool_call in response_message.tool_calls:
                    func_name = tool_call.function.name
                    func_args = json.loads(tool_call.function.arguments or "{}")

                    if on_tool_call:
                        on_tool_call(func_name, func_args)

                    result_text = await self.mcp.execute_tool(func_name, func_args)

                    self.messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": func_name,
                            "content": str(result_text),
                        }
                    )

        except Exception as e:  # noqa: BLE001
            print("Error in Groq chat.completions.create:", type(e).__name__, e)
            return None

    def get_system_prompt(self):
        candidates = [
            Path(getattr(sys, "_MEIPASS", "")),
            Path(__file__).resolve().parent,
            Path.cwd(),
        ]
        prompt_path = next(
            (
                candidate / "resources" / "prompts" / "systemprompt1.txt"
                for candidate in candidates
                if candidate
                and (candidate / "resources" / "prompts" / "systemprompt1.txt").is_file()
            ),
            Path("resources/prompts/systemprompt1.txt"),
        )
        with prompt_path.open("r", encoding="utf-8") as file:
            content = file.read()
        return content

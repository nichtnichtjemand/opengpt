import json
import locale
import logging
import platform
import sys
import uuid
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

import json_repair
from google import genai
from groq import AsyncGroq, BadRequestError

from config import get_api_key, load_api_keys
from mcp_manager import MCPManager
from resources.mcp.tools.skills.skillmanager import get_skills

logger = logging.getLogger("opengpt." + __name__)


def bundle_root() -> Path:
    start_candidates = [
        Path(getattr(sys, "_MEIPASS", "")),
        Path(__file__).resolve(),
        Path.cwd(),
    ]
    for start in start_candidates:
        if not start or not str(start):
            continue
        start = start if start.is_dir() else start.parent
        for candidate in (start, *start.parents):
            prompt = candidate / "resources" / "prompts" / "systemprompt1.txt"
            if prompt.is_file():
                return candidate
    return Path(__file__).resolve().parent


load_api_keys()

google_client = None
groq_client = None


def reset_api_clients() -> None:
    global google_client, groq_client
    google_client = None
    groq_client = None


def get_groq_client() -> AsyncGroq:
    global groq_client
    api_key = get_api_key("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is not configured.")
    if groq_client is None:
        groq_client = AsyncGroq(api_key=api_key, timeout=30.0)
    return groq_client


def get_google_client():
    global google_client
    api_key = get_api_key("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY is not configured.")
    if google_client is None:
        google_client = genai.Client(
            api_key=api_key,
            http_options={"timeout": 30000},
        )
    return google_client


class GenerationError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class Conversation:
    def __init__(
        self,
        mcp: MCPManager,
        provider: str = "google",
        model: str = "gemini-3.5-flash-lite",
    ):
        self.mcp = mcp
        self.provider = provider.lower()
        self.model = model

        self.system_prompt = self.get_system_prompt()

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
            raise ValueError(f"Unknown Provider: {self.provider}")

    async def _send_google(
        self, message: str, on_tool_call: Callable[[str, dict], None] | None = None
    ) -> str | None:
        google_client = get_google_client()
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

                interaction = await google_client.aio.interactions.create(**kwargs)
                if interaction.errors != None:
                    logger.error("Error: " + str(interaction.errors))
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
            logger.error(f"Error in Google interactions.create: {e}")
            return f"Error in Google interactions.create: {e}"

    async def _send_groq(
        self, message: str, on_tool_call: Callable[[str, dict], None] | None = None
    ) -> str | None:
        groq_client = get_groq_client()
        self.messages.append({"role": "user", "content": message})
        groq_tools = getattr(self.mcp, "openai_tools", None)

        while True:
            kwargs = {
                "model": self.model,
                "messages": self.messages,
                "temperature": 0.3,
                "max_completion_tokens": 4096,
                "top_p": 1.0,
                "stream": False,
            }

            if "gpt-oss" in self.model or "qwen3" in self.model:
                kwargs["reasoning_effort"] = "medium"

            if groq_tools:
                kwargs["tools"] = groq_tools

            try:
                completion = await groq_client.chat.completions.create(**kwargs)
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
                calls_to_run = [
                    (
                        tc.id,
                        tc.function.name,
                        json.loads(tc.function.arguments or "{}"),
                    )
                    for tc in response_message.tool_calls
                ]

            except BadRequestError as e:
                logger.error(f"Error in Groq chat.completions.create: {e}")
                error_info = e.body.get("error", {}) if isinstance(e.body, dict) else {}

                if error_info.get("code") == "tool_use_failed":
                    failed_raw = error_info.get("failed_generation", "")
                    repaired = json_repair.loads(failed_raw)

                    if (
                        not isinstance(repaired, dict)
                        or "name" not in repaired
                        or "arguments" not in repaired
                    ):
                        raise e  # noqa: TRY201

                    func_name = repaired["name"]
                    func_args = repaired["arguments"]
                    if isinstance(func_args, str):
                        func_args = json_repair.loads(func_args)

                    fake_call_id = f"call_repaired_{uuid.uuid4().hex[:8]}"

                    self.messages.append(
                        {
                            "role": "assistant",
                            "content": "",
                            "tool_calls": [
                                {
                                    "id": fake_call_id,
                                    "type": "function",
                                    "function": {
                                        "name": func_name,
                                        "arguments": json.dumps(func_args),
                                    },
                                }
                            ],
                        }
                    )

                    calls_to_run = [(fake_call_id, func_name, func_args)]
                else:
                    raise

            for call_id, func_name, func_args in calls_to_run:
                if on_tool_call:
                    on_tool_call(func_name, func_args)

                result_text = await self.mcp.execute_tool(func_name, func_args)

                self.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call_id,
                        "name": func_name,
                        "content": str(result_text),
                    }
                )

    def get_system_prompt(self):
        prompt_path = bundle_root() / "resources" / "prompts" / "systemprompt1.txt"
        with prompt_path.open("r", encoding="utf-8") as file:
            content = file.read()

        return self.format_system_prompt(content)

    def format_system_prompt(self, prompt: str):
        prompt = (
            prompt.replace("{SYSTEM:MODEL}", self.model)
            .replace("{SYSTEM:TIME}", datetime.now().strftime("%d.%m.%Y %H:%M:%S"))
            .replace("{SYSTEM:PLATFORM}", str(platform.uname()))
            .replace("{SYSTEM:LOCALE}", str(locale.getdefaultlocale()))
            + f"\n\nAvailable Skills: {get_skills()}"
        )
        return prompt

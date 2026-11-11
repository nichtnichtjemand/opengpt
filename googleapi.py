import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")


client = genai.Client(api_key=api_key, http_options={"timeout": 30000})


class Conversation:
    def __init__(self):
        self.conversation_id = None
        self.system_prompt = self.get_system_prompt()

    def send_message(self, message: str) -> str | None:

        generation_config = {
            "max_output_tokens": 65536,
            "thinking_level": "minimal",
        }

        try:
            if self.conversation_id == None:
                interaction = client.interactions.create(
                    model="gemini-3.5-flash-lite",
                    input=message,
                    generation_config=generation_config,
                    system_instruction=self.system_prompt,
                )
            else:
                interaction = client.interactions.create(
                    model="gemini-3.5-flash-lite",
                    input=message,
                    generation_config=generation_config,
                    previous_interaction_id=self.conversation_id,
                    system_instruction=self.system_prompt,
                )
            self.conversation_id = interaction.id
            return interaction.output_text

        except Exception as e:
            print("Error in interactions.create:", type(e).__name__, e)
            return None

    def get_system_prompt(self):
        with open("resources/prompts/systemprompt1.txt", "r", encoding="utf-8") as file:
            content = file.read()
        return content

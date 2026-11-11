from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")

client = genai.Client(
    api_key=api_key,
    http_options={"timeout": 20000}
)

def send_message(message: str) -> str | None:

    generation_config = {
        "max_output_tokens": 65536,
        "thinking_level": "low",
    }

    try:
        interaction = client.interactions.create(
            model="gemini-3.5-flash-lite",
            input=message,
            generation_config=generation_config,
        )
        return interaction.output_text

    except Exception as e:
        print("Error in interactions.create:", type(e).__name__, e)
        return None

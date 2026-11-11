from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")


client = genai.Client(
    api_key=api_key,
    http_options={"timeout": 20000}
)

class Conversation: 

    

    def __init__(self):
        self.conversation_id = None

    def send_message(self, message: str) -> str | None:

        generation_config = {
            "max_output_tokens": 65536,
            "thinking_level": "low",
        }

        try:
            if self.conversation_id == None:
            
                interaction = client.interactions.create(
                    model="gemini-3.5-flash-lite",
                    input=message,
                    generation_config=generation_config,
                )
            else: 
                interaction = client.interactions.create(
                    model="gemini-3.5-flash-lite",
                    input=message,
                    generation_config=generation_config,
                    previous_interaction_id=self.conversation_id
                )
            self.conversation_id = interaction.id
            return interaction.output_text

        except Exception as e:
            print("Error in interactions.create:", type(e).__name__, e)
            return None

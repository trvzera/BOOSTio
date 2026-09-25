from google import genai
from dotenv import get_env

client = genai.Client(api_key=get_env("GEMINI_API_KEY"))

class LLMService:
  def executar(self,prompt:str):
    interaction = client.interactions.create(
      model="gemini-3.8-flash",
      input=prompt
    )
    return interaction.output_text

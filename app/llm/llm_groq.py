from llm_client import BaseLLMClient
from groq import Groq

class GroqClient(BaseLLMClient):
    def __init__(self, api_key):
        self.client = Groq(api_key=api_key)

    def chat(self, prompt: str, **kwargs):
        return self.client.chat(prompt, **kwargs)

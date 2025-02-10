from llm_client import BaseLLMClient
import openai

class OpenAIClient(BaseLLMClient):
    def __init__(self, api_key):
        self.api_key = api_key

    def chat(self, prompt: str, **kwargs):
        openai.api_key = self.api_key
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        return response

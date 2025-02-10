class BaseLLMClient:
    def chat(self, prompt: str, **kwargs):
        raise NotImplementedError("Subclasses must implement this method.")

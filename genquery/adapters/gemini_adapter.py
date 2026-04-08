from .base import LLMAdapter, Message
from typing import Any, List

class GeminiAdapter(LLMAdapter):
    def __init__(self, api_key: str, model: str = "gemini-1.5-pro"):
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)

    def complete(self, messages: List[Message], **kwargs: Any) -> str:
        # Standardize standard roles to gemini roles or just pass string if using generate_content straightforwardly
        prompt = "\n".join([f"{m.role}: {m.content}" for m in messages])
        response = self.model.generate_content(prompt, **kwargs)
        return response.text

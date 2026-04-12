import openai
from .base import LLMAdapter, Message
from typing import Any, List

class OpenAIAdapter(LLMAdapter):
    def __init__(self, api_key: str, model: str, base_url: str = "https://api.openai.com/v1"):
        self.client = openai.OpenAI(base_url=base_url, api_key=api_key)
        self.model = model

    def complete(self, messages: List[Message], **kwargs: Any) -> str:
        formatted_messages = [{"role": m.role, "content": m.content} for m in messages]
        response = self.client.chat.completions.create(
            model=self.model,
            messages=formatted_messages, # type: ignore
            **kwargs
        )
        return response.choices[0].message.content or ""

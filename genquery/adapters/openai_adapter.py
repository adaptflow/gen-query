import openai
from .base import LLMAdapter, Message
from typing import Any, List

class OpenAIAdapter(LLMAdapter):
    """
    Adapter for OpenAI's language models.
    """
    def __init__(self, api_key: str, model: str, base_url: str = "https://api.openai.com/v1"):
        """
        Initialize the OpenAI adapter.
        
        Args:
            api_key: The OpenAI API key.
            model: The model name to use (e.g., 'gpt-4').
            base_url: The base URL for the API.
        """
        self.client = openai.OpenAI(base_url=base_url, api_key=api_key)
        self.model = model

    def complete(self, messages: List[Message], **kwargs: Any) -> str:
        """
        Generate completion for the given messages.
        
        Args:
            messages: List of messages for the conversation.
            **kwargs: Additional arguments to pass to the API.
            
        Returns:
            The generated response string.
        """
        formatted_messages = [{"role": m.role, "content": m.content} for m in messages]
        response = self.client.chat.completions.create(
            model=self.model,
            messages=formatted_messages, # type: ignore
            **kwargs
        )
        return response.choices[0].message.content or ""

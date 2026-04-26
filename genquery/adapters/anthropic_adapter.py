from .base import LLMAdapter, Message
from typing import Any, List

class AnthropicAdapter(LLMAdapter):
    """
    Adapter for Anthropic's Claude language models.
    """
    def __init__(self, api_key: str, model: str = "claude-3-opus-20240229"):
        """
        Initialize the Anthropic adapter.
        
        Args:
            api_key: The Anthropic API key.
            model: The model name to use.
        """
        import anthropic
        self.client = anthropic.Anthropic(api_key=api_key)
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
        formatted_messages = [{"role": m.role, "content": m.content} for m in messages if m.role != "system"]
        system_msg = next((m.content for m in messages if m.role == "system"), "")
        
        response = self.client.messages.create(
            model=self.model,
            system=system_msg,
            messages=formatted_messages, # type: ignore
            **kwargs
        )
        return response.content[0].text

from .base import LLMAdapter, Message
from typing import Any, List

class OllamaAdapter(LLMAdapter):
    """
    Adapter for Ollama local language models.
    """
    def __init__(self, host: str = "http://localhost:11434", model: str = "llama3"):
        """
        Initialize the Ollama adapter.
        
        Args:
            host: The Ollama server URL.
            model: The model name to use.
        """
        self.host = host
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
        import requests
        formatted_messages = [{"role": m.role, "content": m.content} for m in messages]
        
        payload = {
            "model": self.model,
            "messages": formatted_messages,
            "stream": False,
            **kwargs
        }
        
        response = requests.post(f"{self.host}/api/chat", json=payload)
        response.raise_for_status()
        return response.json().get("message", {}).get("content", "")

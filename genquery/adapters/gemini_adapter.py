from .base import AsyncLLMAdapter, LLMAdapter, Message
from typing import Any, List

class GeminiAdapter(LLMAdapter):
    """
    Adapter for Google's Gemini language models.
    """
    def __init__(self, api_key: str, model: str = "gemini-1.5-pro"):
        """
        Initialize the Gemini adapter.
        
        Args:
            api_key: The Google API key.
            model: The model name to use.
        """
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)

    def complete(self, messages: List[Message], **kwargs: Any) -> str:
        """
        Generate completion for the given messages.
        
        Args:
            messages: List of messages for the conversation.
            **kwargs: Additional arguments to pass to the API.
            
        Returns:
            The generated response string.
        """
        # Standardize standard roles to gemini roles or just pass string if using generate_content straightforwardly
        prompt = "\n".join([f"{m.role}: {m.content}" for m in messages])
        response = self.model.generate_content(prompt, **kwargs)
        return response.text

class AsyncGeminiAdapter(AsyncLLMAdapter):
    """
    Async adapter for Google's Gemini language models.
    """
    def __init__(self, api_key: str, model: str = "gemini-1.5-pro"):
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)

    async def acomplete(self, messages: List[Message], **kwargs: Any) -> str:
        """Asynchronously generate completion for the given messages."""
        prompt = "\n".join([f"{m.role}: {m.content}" for m in messages])
        response = await self.model.generate_content_async(prompt, **kwargs)
        return response.text

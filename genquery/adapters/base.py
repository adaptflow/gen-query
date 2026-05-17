from typing import Protocol, List, Any
from pydantic import BaseModel

class Message(BaseModel):
    """
    Represents a single message in a conversation.
    """
    role: str
    content: str

class LLMAdapter(Protocol):
    """
    Protocol defining the interface for synchronous Language Model adapters.
    """
    def complete(self, messages: List[Message], **kwargs: Any) -> str:
        """Generate completion for the given messages."""
        ...

class AsyncLLMAdapter(Protocol):
    """
    Protocol defining the interface for asynchronous Language Model adapters.
    """
    async def acomplete(self, messages: List[Message], **kwargs: Any) -> str:
        """Asynchronously generate completion for the given messages."""
        ...

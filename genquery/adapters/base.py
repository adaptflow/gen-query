from typing import Protocol, List, Dict, Any
from pydantic import BaseModel

class Message(BaseModel):
    """
    Represents a single message in a conversation.
    """
    role: str
    content: str

class LLMAdapter(Protocol):
    """
    Protocol defining the interface for Language Model adapters.
    """
    def complete(self, messages: List[Message], **kwargs: Any) -> str:
        """Generate completion for the given messages."""
        ...

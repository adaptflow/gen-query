from typing import Protocol, List, Dict, Any
from pydantic import BaseModel

class Message(BaseModel):
    role: str
    content: str

class LLMAdapter(Protocol):
    def complete(self, messages: List[Message], **kwargs: Any) -> str:
        """Generate completion for the given messages."""
        ...

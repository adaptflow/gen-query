from .base import LLMAdapter, Message
from typing import Any, List

class LangChainAdapter(LLMAdapter):
    """
    Adapter for integrating LangChain BaseChatModel or Runnable.
    """
    def __init__(self, runnable: Any):
        """
        Initialize the LangChain adapter.
        
        Args:
            runnable: A LangChain runnable or model instance.
        """
        # Wraps a LangChain BaseChatModel or Runnable
        self.runnable = runnable

    def complete(self, messages: List[Message], **kwargs: Any) -> str:
        """
        Generate completion for the given messages using LangChain.
        
        Args:
            messages: List of messages for the conversation.
            **kwargs: Additional arguments to pass to the runnable.
            
        Returns:
            The generated response string.
        """
        from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
        
        lc_messages: List[BaseMessage] = []
        for m in messages:
            if m.role == "system":
                lc_messages.append(SystemMessage(content=m.content))
            elif m.role == "assistant":
                lc_messages.append(AIMessage(content=m.content))
            else:
                lc_messages.append(HumanMessage(content=m.content))
                
        response = self.runnable.invoke(lc_messages, **kwargs)
        return str(response.content)

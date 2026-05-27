---
title: LLM Adapters API
---

# LLM Adapters API

LLM adapters provide the model interface used by GenQuery pipeline stages.

## Adapter protocols

```python imports.py
from genquery.adapters.base import Message, LLMAdapter, AsyncLLMAdapter
```

### `Message`

```python signature.py
Message(role, content)
```

| Field | Type | Description |
|---|---|---|
| `role` | `str` | Message role, such as `system`, `user`, or `assistant`. |
| `content` | `str` | Message content. |

### `LLMAdapter`

Synchronous adapter protocol.

```python signature.py
class LLMAdapter:
    def complete(self, messages, **kwargs) -> str:
        ...
```

### `AsyncLLMAdapter`

Asynchronous adapter protocol.

```python signature.py
class AsyncLLMAdapter:
    async def acomplete(self, messages, **kwargs) -> str:
        ...
```

## OpenAI adapters

```python imports.py
from genquery.adapters.openai_adapter import OpenAIAdapter, AsyncOpenAIAdapter
```

```python signature.py
OpenAIAdapter(api_key, model, base_url="https://api.openai.com/v1")
AsyncOpenAIAdapter(api_key, model, base_url="https://api.openai.com/v1")
```

Use these with OpenAI or OpenAI-compatible APIs.

```python openai_adapter.py
llm = OpenAIAdapter(api_key="sk-...", model="gpt-5.5")
async_llm = AsyncOpenAIAdapter(api_key="sk-...", model="gpt-5-mini")
```

## Anthropic adapters

```python imports.py
from genquery.adapters.anthropic_adapter import AnthropicAdapter, AsyncAnthropicAdapter
```

```python signature.py
AnthropicAdapter(api_key, model="claude-3-opus-20240229")
AsyncAnthropicAdapter(api_key, model="claude-3-opus-20240229")
```

## Gemini adapters

```python imports.py
from genquery.adapters.gemini_adapter import GeminiAdapter, AsyncGeminiAdapter
```

```python signature.py
GeminiAdapter(api_key, model="gemini-1.5-pro")
AsyncGeminiAdapter(api_key, model="gemini-1.5-pro")
```

## Ollama adapters

```python imports.py
from genquery.adapters.ollama_adapter import OllamaAdapter, AsyncOllamaAdapter
```

```python signature.py
OllamaAdapter(host="http://localhost:11434", model="llama3")
AsyncOllamaAdapter(host="http://localhost:11434", model="llama3")
```

The async Ollama adapter uses a worker thread for the HTTP request to avoid blocking the event loop without adding another required HTTP client dependency.

## LangChain adapters

```python imports.py
from genquery.adapters.langchain_adapter import LangChainAdapter, AsyncLangChainAdapter
```

```python signature.py
LangChainAdapter(runnable)
AsyncLangChainAdapter(runnable)
```

The `runnable` should be a LangChain chat model or runnable. The async adapter uses `ainvoke()` when available and falls back to running `invoke()` in a worker thread.

## Implementing a custom adapter

```python custom_adapter.py
from genquery.adapters.base import Message

class MyAdapter:
    def complete(self, messages: list[Message], **kwargs) -> str:
        return my_model_call(messages, **kwargs)
```

For async:

```python async_custom_adapter.py
from genquery.adapters.base import Message

class MyAsyncAdapter:
    async def acomplete(self, messages: list[Message], **kwargs) -> str:
        return await my_async_model_call(messages, **kwargs)
```

## Related pages

- [GenQuery](./genquery.md)
- [AsyncGenQuery](./async-genquery.md)

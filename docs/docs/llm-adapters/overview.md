---
title: LLM Adapters
---

# LLM Adapters

GenQuery includes synchronous and asynchronous adapters for common LLM providers.

## Supported synchronous adapters

- `OpenAIAdapter`
- `AnthropicAdapter`
- `GeminiAdapter`
- `OllamaAdapter`
- `LangChainAdapter`

## Supported asynchronous adapters

- `AsyncOpenAIAdapter`
- `AsyncAnthropicAdapter`
- `AsyncGeminiAdapter`
- `AsyncOllamaAdapter`
- `AsyncLangChainAdapter`

## Example

```python llm_adapters.py
from genquery.adapters.openai_adapter import OpenAIAdapter, AsyncOpenAIAdapter

sync_llm = OpenAIAdapter(api_key="sk-...", model="gpt-5-mini")
async_llm = AsyncOpenAIAdapter(api_key="sk-...", model="gpt-5-mini")
```

Use sync adapters with `GenQuery` and async adapters with `AsyncGenQuery`.

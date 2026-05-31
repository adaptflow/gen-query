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

## Provider package requirements

OpenAI support is included with the base package dependencies. Other adapters import their provider package only when used:

| Adapter family | Required package |
|---|---|
| Anthropic | `anthropic` |
| Gemini | `google-generativeai` |
| Ollama | `requests` and a running Ollama server |
| LangChain | `langchain-core` plus the LangChain integration package for your model |

Install only what you need, for example:

```bash terminal
pip install anthropic
pip install google-generativeai
pip install requests
pip install langchain langchain-core
```

## Example

```python llm_adapters.py
from genquery.adapters.openai_adapter import OpenAIAdapter, AsyncOpenAIAdapter

sync_llm = OpenAIAdapter(api_key="sk-...", model="gpt-5-mini")
async_llm = AsyncOpenAIAdapter(api_key="sk-...", model="gpt-5-mini")
```

Use sync adapters with `GenQuery` and async adapters with `AsyncGenQuery`.

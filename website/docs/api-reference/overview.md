---
title: API Reference Overview
---

# API Reference Overview

This API reference documents the public classes, protocols, configuration models, and extension points that users are most likely to use when integrating GenQuery.

:::info
The package currently exports `GenQuery`, `AsyncGenQuery`, and `configure_logging` from `genquery`. Other public classes are imported from their module paths shown below.
:::

## Top-level imports

```python imports.py
from genquery import GenQuery, AsyncGenQuery, configure_logging
```

## Reference pages

| Page | Covers |
|---|---|
| [GenQuery](./genquery.md) | Synchronous orchestrator and query methods. |
| [AsyncGenQuery](./async-genquery.md) | Async orchestrator, lifecycle, and query methods. |
| [QueryResult](./query-result.md) | Result object returned by `generate()`, `dry_run()`, `stream()`, and `run(..., return_result=True)`. |
| [Configuration](./configuration.md) | `GenQueryConfig`, `TableFilterConfig`, `RLSPolicy`, and `PromptsConfig`. |
| [Models](./models.md) | Pydantic models for conversation, schema, and query plans. |
| [LLM Adapters](./llm-adapters.md) | Adapter protocols and built-in provider adapters. |
| [Callbacks](./callbacks.md) | Sync and async callback handlers for observability. |
| [Pipeline](./pipeline.md) | Pipeline stages, state, and stage manager APIs. |
| [Logging](./logging.md) | `configure_logging()`, `normalize_log_level()`, and `get_logger()`. |

## Version

The current package version is `0.1.0`.

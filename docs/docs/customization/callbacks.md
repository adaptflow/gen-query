---
title: Callbacks and Observability
---

# Callbacks and Observability

Use callbacks to observe pipeline execution and integrate GenQuery with logging, tracing, metrics, or audit systems.

## Sync callbacks

```python callbacks.py
from genquery.core.callbacks import GenQueryCallbackHandler

class MyLogger(GenQueryCallbackHandler):
    def on_sql_generated(self, step_id: str, sql: str) -> None:
        print(f"Generated SQL for {step_id}: {sql}")

gq = GenQuery(llm=llm, connection_string="...", callbacks=MyLogger())
```

## Async callbacks

Use `AsyncGenQueryCallbackHandler` for async pipelines.

```python async_callbacks.py
from genquery import AsyncGenQuery
from genquery.core.callbacks import AsyncGenQueryCallbackHandler

class MyAsyncLogger(AsyncGenQueryCallbackHandler):
    async def aon_sql_generated(self, step_id: str, sql: str) -> None:
        await write_log_async(f"Generated SQL for {step_id}: {sql}")

gq = AsyncGenQuery(
    llm=async_llm,
    connection_string="postgresql+asyncpg://...",
    callbacks=MyAsyncLogger(),
)
```

Async callbacks are additive to sync callbacks. The default async methods call the corresponding sync methods, so you can override sync methods for lightweight logging or async methods for non-blocking work.

## Lightweight logging in async pipelines

```python lightweight_async_callbacks.py
from genquery.core.callbacks import AsyncGenQueryCallbackHandler

class MyLogger(AsyncGenQueryCallbackHandler):
    def on_sql_generated(self, step_id: str, sql: str) -> None:
        print(f"Generated SQL for {step_id}: {sql}")
```

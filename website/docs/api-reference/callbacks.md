---
title: Callbacks API
---

# Callbacks API

Callbacks let you observe GenQuery pipeline events without replacing pipeline stages.

## Imports

```python imports.py
from genquery.core.callbacks import (
    GenQueryCallbackHandler,
    AsyncGenQueryCallbackHandler,
    AsyncCallbackAdapter,
    ensure_async_callback_handler,
)
```

## `GenQueryCallbackHandler`

Base synchronous callback handler. Subclass it and override the methods you need.

```python callback_handler.py
from genquery.core.callbacks import GenQueryCallbackHandler

class MyCallbacks(GenQueryCallbackHandler):
    def on_sql_generated(self, step_id: str, sql: str) -> None:
        print(step_id, sql)
```

### Methods

| Method | Called when |
|---|---|
| `on_inspector_start()` | Schema inspector begins. |
| `on_inspector_end(tables_found)` | Schema inspector ends. |
| `on_adapter_call(prompt)` | Before an LLM adapter is invoked. |
| `on_adapter_response(response)` | After an LLM adapter returns a response. |
| `on_ranker_start(query)` | Semantic ranker begins. |
| `on_ranker_end(num_tables)` | Semantic ranker ends. |
| `on_planner_start(query)` | Query planner begins. |
| `on_planner_end(plan)` | Query planner ends. |
| `on_sql_generated(step_id, sql)` | SQL is generated for a plan step. |
| `on_retry(step_id, error, attempt)` | Execution is retried. |
| `on_execution_success(step_id, row_count)` | Execution succeeds. |

## `AsyncGenQueryCallbackHandler`

Async callback handler for async pipelines.

```python async_callback_handler.py
from genquery.core.callbacks import AsyncGenQueryCallbackHandler

class MyAsyncCallbacks(AsyncGenQueryCallbackHandler):
    async def aon_sql_generated(self, step_id: str, sql: str) -> None:
        await write_audit_log(step_id, sql)
```

### Async methods

| Method | Delegates to sync method by default |
|---|---|
| `aon_inspector_start()` | `on_inspector_start()` |
| `aon_inspector_end(tables_found)` | `on_inspector_end(tables_found)` |
| `aon_adapter_call(prompt)` | `on_adapter_call(prompt)` |
| `aon_adapter_response(response)` | `on_adapter_response(response)` |
| `aon_ranker_start(query)` | `on_ranker_start(query)` |
| `aon_ranker_end(num_tables)` | `on_ranker_end(num_tables)` |
| `aon_planner_start(query)` | `on_planner_start(query)` |
| `aon_planner_end(plan)` | `on_planner_end(plan)` |
| `aon_sql_generated(step_id, sql)` | `on_sql_generated(step_id, sql)` |
| `aon_retry(step_id, error, attempt)` | `on_retry(step_id, error, attempt)` |
| `aon_execution_success(step_id, row_count)` | `on_execution_success(step_id, row_count)` |

## `AsyncCallbackAdapter`

Wraps a synchronous callback handler for use in async pipelines.

```python async_adapter.py
sync_callbacks = MyCallbacks()
async_callbacks = AsyncCallbackAdapter(sync_callbacks)
```

Most users do not need to instantiate this directly because `AsyncGenQuery` calls `ensure_async_callback_handler()` internally.

## `ensure_async_callback_handler()`

```python signature.py
ensure_async_callback_handler(callbacks=None)
```

Returns an async callback handler:

- If `callbacks` is `None`, returns `AsyncGenQueryCallbackHandler()`.
- If `callbacks` already has async callback methods, returns it unchanged.
- Otherwise wraps the sync handler in `AsyncCallbackAdapter`.

## Related pages

- [Callbacks and Observability](../customization/callbacks.md)
- [GenQuery](./genquery.md)
- [AsyncGenQuery](./async-genquery.md)

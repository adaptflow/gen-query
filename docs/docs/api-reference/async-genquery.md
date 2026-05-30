---
title: AsyncGenQuery
---

# AsyncGenQuery

`AsyncGenQuery` is the asyncio-compatible orchestrator for natural-language to SQL generation and execution.

## Import

```python imports.py
from genquery import AsyncGenQuery
```

## Constructor

```python signature.py
AsyncGenQuery(
    llm,
    connection_string=None,
    schema="public",
    config=None,
    connect_args=None,
    table_filter=None,
    config_path=None,
    callbacks=None,
    custom_stages=None,
    engine=None,
    log_level=None,
)
```

## Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `llm` | `AsyncLLMAdapter` | Required | Async LLM adapter used by async pipeline stages. |
| `connection_string` | `str \| None` | `None` | Async SQLAlchemy database URL. Required unless supplied by `config`, `config_path`, or `engine`. |
| `schema` | `str` | `"public"` | Database schema name. |
| `config` | `GenQueryConfig \| None` | `None` | Full configuration object. Takes precedence over individual parameters. |
| `connect_args` | `dict \| None` | `None` | Extra arguments passed to SQLAlchemy `create_async_engine()`. |
| `table_filter` | `dict \| None` | `None` | Convenience dictionary used to build `TableFilterConfig`. |
| `config_path` | `str \| None` | `None` | Path to a YAML config file. |
| `callbacks` | `AsyncGenQueryCallbackHandler \| GenQueryCallbackHandler \| None` | `None` | Async callbacks or sync callbacks that will be wrapped. |
| `custom_stages` | `list[AsyncPipelineStage] \| None` | `None` | Custom async stages to use instead of the default pipeline. |
| `engine` | `AsyncEngine \| None` | `None` | Existing SQLAlchemy async engine. |
| `log_level` | `str \| int \| None` | `None` | Logging level override. |

## Recommended lifecycle

Use `AsyncGenQuery` as an async context manager so pooled database connections are disposed automatically.

```python lifecycle.py
async with AsyncGenQuery(
    llm=async_llm,
    connection_string="postgresql+asyncpg://user:pass@localhost:5432/mydb",
) as gq:
    df = await gq.run("Count orders by status")
```

If you do not use a context manager, call `close()` when the instance is no longer needed.

```python close.py
gq = AsyncGenQuery(llm=async_llm, connection_string="sqlite+aiosqlite:///app.db")
try:
    result = await gq.run("Count orders", return_result=True)
finally:
    await gq.close()
```

## Methods

### `run()`

```python signature.py
await gq.run(query, conversation=None, return_result=False)
```

Generates SQL, validates it, executes it asynchronously, and returns a Polars DataFrame by default.

```python run.py
df = await gq.run("Count orders by status")

result = await gq.run("Count orders by status", return_result=True)
print(result.sql)
print(result.df)
```

### `generate()`

```python signature.py
await gq.generate(query, conversation=None)
```

Executes the full async pipeline and always returns a `QueryResult`.

```python generate.py
result = await gq.generate("Show revenue by month")
print(result.sql)
print(result.df)
```

### `dry_run()`

```python signature.py
await gq.dry_run(query, conversation=None)
```

Generates SQL and an execution plan without executing the final query.

```python dry_run.py
result = await gq.dry_run("Show top customers this year")
print(result.sql)
```

### `stream()`

```python signature.py
await gq.stream(query, conversation=None, batch_size=None)
```

Returns a `QueryResult` whose `stream` is an async final-result stream.

```python stream.py
result = await gq.stream("Show all orders from this year", batch_size=5000)

async with result.stream as batches:
    async for batch in batches:
        print(batch)
```

### `close()`

```python signature.py
await gq.close()
```

Disposes the async SQLAlchemy engine and closes pooled connections.

## Attributes

| Attribute | Description |
|---|---|
| `config` | Resolved `GenQueryConfig`. |
| `llm` | Async LLM adapter instance. |
| `callbacks` | Async callback handler. |
| `engine` | SQLAlchemy `AsyncEngine`. |
| `validator` | Security validator used by the executor. |
| `pipeline` | `AsyncGenQueryPipeline` instance. |

## Related pages

- [GenQuery](./genquery.md)
- [QueryResult](./query-result.md)
- [Configuration](./configuration.md)
- [Callbacks](./callbacks.md)

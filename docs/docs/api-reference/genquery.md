---
title: GenQuery
---

# GenQuery

`GenQuery` is the synchronous orchestrator for natural-language to SQL generation and execution.

## Import

```python imports.py
from genquery import GenQuery
```

## Constructor

```python signature.py
GenQuery(
    llm,
    connection_string=None,
    schema="public",
    config=None,
    connect_args=None,
    table_filter=None,
    config_path=None,
    callbacks=None,
    custom_stages=None,
    log_level=None,
)
```

## Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `llm` | `LLMAdapter` | Required | Synchronous LLM adapter used by ranker, planner, and executor stages. |
| `connection_string` | `str \| None` | `None` | SQLAlchemy database URL. Required unless supplied by `config` or `config_path`. |
| `schema` | `str` | `"public"` | Database schema name. |
| `config` | `GenQueryConfig \| None` | `None` | Full configuration object. Takes precedence over individual parameters. |
| `connect_args` | `dict \| None` | `None` | Extra arguments passed to SQLAlchemy `create_engine()`. |
| `table_filter` | `dict \| None` | `None` | Convenience dictionary used to build `TableFilterConfig`. |
| `config_path` | `str \| None` | `None` | Path to a YAML config file. |
| `callbacks` | `GenQueryCallbackHandler \| None` | `None` | Callback handler for observability events. |
| `custom_stages` | `list[PipelineStage] \| None` | `None` | Custom stages to use instead of the default pipeline. |
| `log_level` | `str \| int \| None` | `None` | Logging level override. |

## Configuration priority

`GenQuery` resolves configuration in this order:

1. `config`
2. `config_path`
3. Individual constructor parameters

If `connect_args` or `log_level` are supplied with `config` or `config_path`, they override or merge into the resolved configuration.

## Methods

### `run()`

```python signature.py
gq.run(query, conversation=None, return_result=False)
```

Generates SQL, validates it, executes it, and returns a Polars DataFrame by default.

Set `return_result=True` to return a `QueryResult`.

```python run.py
df = gq.run("Count orders by status")

result = gq.run("Count orders by status", return_result=True)
print(result.sql)
print(result.df)
```

### `generate()`

```python signature.py
gq.generate(query, conversation=None)
```

Executes the full pipeline and always returns a `QueryResult`.

```python generate.py
result = gq.generate("Show revenue by month")
print(result.sql)
print(result.df)
```

### `dry_run()`

```python signature.py
gq.dry_run(query, conversation=None)
```

Generates SQL and an execution plan without running the final SQL as a data-returning query. The returned `QueryResult` contains `sql`, `plan`, and `steps`; `df` contains the database's `EXPLAIN` output and `stream` is `None`.

```python dry_run.py
result = gq.dry_run("Show top customers this year")
print(result.sql)
```

### `stream()`

```python signature.py
gq.stream(query, conversation=None, batch_size=None)
```

Executes the pipeline and returns a `QueryResult` whose `stream` yields Polars DataFrame batches for the final result.

```python stream.py
result = gq.stream("Show all orders from this year", batch_size=5000)

with result.stream as batches:
    for batch in batches:
        print(batch)
```

## Attributes

| Attribute | Description |
|---|---|
| `config` | Resolved `GenQueryConfig`. |
| `llm` | LLM adapter instance. |
| `callbacks` | Callback handler. |
| `engine` | SQLAlchemy synchronous engine. |
| `validator` | Security validator used by the executor. |
| `pipeline` | `GenQueryPipeline` instance. |

## Conversation context

The `conversation` argument accepts a list of `ConversationTurn` objects. This lets ranker, planner, and executor prompts consider prior user requests and generated artifacts.

```python conversation.py
from genquery.core.models import ConversationTurn

conversation = [
    ConversationTurn(
        user_query="Show revenue by month",
        sql="SELECT ...",
        result_summary="12 monthly rows",
    )
]

result = gq.run("Now only show this year", conversation=conversation, return_result=True)
```

## Related pages

- [AsyncGenQuery](./async-genquery.md)
- [QueryResult](./query-result.md)
- [Configuration](./configuration.md)
- [Callbacks](./callbacks.md)

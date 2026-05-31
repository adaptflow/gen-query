---
title: QueryResult
---

# QueryResult

`QueryResult` represents the final public result of a GenQuery pipeline execution.

## Import

```python imports.py
from genquery.pipeline.pipeline import QueryResult
```

Most users do not instantiate `QueryResult` directly. It is returned by:

- `GenQuery.generate()`
- `GenQuery.dry_run()`
- `GenQuery.stream()`
- `GenQuery.run(..., return_result=True)`
- async equivalents on `AsyncGenQuery`

## Constructor

```python signature.py
QueryResult(
    sql,
    plan,
    steps,
    df=None,
    stream=None,
    conversation=None,
)
```

## Attributes

| Attribute | Type | Description |
|---|---|---|
| `sql` | `str \| None` | Final generated SQL. |
| `plan` | `Any` | Query plan object, usually `QueryPlan`. |
| `steps` | `Any` | Plan steps, usually `list[PlanStep]`. |
| `df` | `Any` | Final Polars DataFrame for non-streaming execution; for dry runs, the database's `EXPLAIN` output. |
| `stream` | `Any` | Sync or async final-result stream. |
| `conversation` | `list[ConversationTurn]` | Updated conversation history. |

## Returned by `run(..., return_result=True)`

```python run_result.py
result = gq.run("Show total revenue by month", return_result=True)

print(result.sql)
print(result.plan)
print(result.steps)
print(result.df)
```

## Returned by `dry_run()`

Dry runs do not run the generated SQL as a normal data-returning query. They execute `EXPLAIN <generated SQL>` and return that explanation in `df`.

```python dry_run_result.py
result = gq.dry_run("Show top customers this year")

print(result.sql)    # generated SQL without the EXPLAIN prefix
print(result.plan)
print(result.steps)
print(result.df)     # Polars DataFrame containing EXPLAIN output
assert result.stream is None
```

## Returned by `stream()`

```python stream_result.py
result = gq.stream("Show all orders", batch_size=5000)

print(result.sql)

with result.stream as batches:
    for batch in batches:
        print(batch)
```

## Conversation history

`conversation` can be passed into a later call for multi-turn follow-up queries.

```python conversation_result.py
first = gq.run("Show revenue by month", return_result=True)
second = gq.run(
    "Now only show this year",
    conversation=first.conversation,
    return_result=True,
)
```

## Related pages

- [Models](./models.md)
- [GenQuery](./genquery.md)
- [AsyncGenQuery](./async-genquery.md)

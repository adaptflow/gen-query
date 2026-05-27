---
title: QueryResult
---

# QueryResult

`QueryResult` is returned by `generate()`, `dry_run()`, `stream()`, and by `run(..., return_result=True)`.

It gives you access to the generated SQL, the execution plan, plan steps, final DataFrame, stream, and related metadata depending on which method you call.

## Common fields

| Field | Description |
|---|---|
| `sql` | Final generated SQL. |
| `plan` | Logical execution plan. |
| `steps` | Individual plan steps. |
| `df` | Final Polars DataFrame for non-streaming execution. |
| `stream` | Final-result stream for streaming execution. |

## Example

```python query_result.py
result = gq.run("Show revenue by month", return_result=True)

print(result.sql)
print(result.plan)
print(result.df)
```

For dry runs, `df` and `stream` are `None` because the SQL is not executed.

---
title: QueryResult
---

# QueryResult

`QueryResult` is returned by `generate()`, `dry_run()`, `stream()`, and by `run(..., return_result=True)`.

It gives you access to the generated SQL, the execution plan, plan steps, final DataFrame, stream, and updated conversation history depending on which method you call.

## Common fields

| Field | Description |
|---|---|
| `sql` | Final generated SQL. |
| `plan` | Logical execution plan. |
| `steps` | Individual plan steps. |
| `df` | Final Polars DataFrame for non-streaming execution; for dry runs, the database's `EXPLAIN` output. |
| `stream` | Final-result stream for streaming execution. |
| `conversation` | Updated list of `ConversationTurn` objects that can be passed into a later call for multi-turn follow-ups. |

## Example

```python query_result.py
result = gq.run("Show revenue by month", return_result=True)

print(result.sql)
print(result.plan)
print(result.df)
```

For dry runs, `stream` is `None`. `df` contains the database's `EXPLAIN` output for the generated SQL, because dry runs validate the generated query with `EXPLAIN` rather than running it as a normal result query.

## Conversation history

Pass `result.conversation` into a later call to give the ranker, planner, and executor context from previous turns.

```python conversation.py
first = gq.run("Show revenue by month", return_result=True)
second = gq.run(
    "Now only show this year",
    conversation=first.conversation,
    return_result=True,
)
```

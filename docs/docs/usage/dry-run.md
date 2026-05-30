---
title: Dry Run
---

# Dry Run

Use `dry_run()` to generate SQL and an execution plan without executing against the database.

Dry runs are useful for debugging, review workflows, approval gates, and understanding how a natural-language query will be interpreted.

## Sync dry run

```python dry_run.py
result = gq.dry_run("Show me the top 5 customers by total order amount this year")

print("Generated SQL:")
print(result.sql)

print("\nExecution Plan Steps:")
for step in result.steps:
    print(f"  - {step.description}")
```

## Async dry run

```python async_dry_run.py
result = await gq.dry_run("Show me the top 5 customers by total order amount this year")

print("Generated SQL:")
print(result.sql)

print("\nExecution Plan Steps:")
for step in result.steps:
    print(f"  - {step.description}")
```

## Behavior

`dry_run()` runs the pipeline through schema inspection, table ranking, SQL generation, and security validation. It then prefixes the generated SQL with `EXPLAIN` instead of executing it.

The returned `QueryResult` includes:

- `sql`
- `plan`
- `steps`

The following fields are `None`:

- `df`
- `stream`

:::info
Dry run does not execute the generated query, but it still needs database access for schema inspection.
:::

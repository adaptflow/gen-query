---
title: Dry Run
---

# Dry Run

Use `dry_run()` to generate SQL and an execution plan without running the generated SQL as a data-returning query.

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

`dry_run()` runs the pipeline through schema inspection, table ranking, SQL generation, security validation, SQL modifiers such as row limits/RLS injection, and then sends an `EXPLAIN <generated SQL>` statement to the database.

The returned `QueryResult` includes:

- `sql`: the generated SQL text, without the `EXPLAIN` prefix.
- `plan`: the logical execution plan.
- `steps`: the individual plan steps.
- `df`: a Polars DataFrame containing the database's `EXPLAIN` output.
- `stream`: always `None` for dry runs.

:::info
Dry run does not run the generated SQL as a normal result query, but it still needs database access for schema inspection and the `EXPLAIN` validation step.
:::

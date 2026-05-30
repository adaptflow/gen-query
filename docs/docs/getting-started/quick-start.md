---
title: Quick Start
---

# Quick Start

This page shows the smallest synchronous GenQuery setup.

## Run a query

```python basic_sync.py
from genquery import GenQuery
from genquery.adapters.openai_adapter import OpenAIAdapter

llm = OpenAIAdapter(api_key="sk-...", model="gpt-5.5")

gq = GenQuery(
    llm=llm,
    connection_string="postgresql://user:pass@localhost:5432/mydb",
    schema="public",
)

df = gq.run("Show me the top 5 customers by total order amount this year")
print(df)
```

`run()` returns a Polars DataFrame by default.

## Return SQL, plan, and DataFrame

Use `return_result=True` when you also want metadata:

```python return_result.py
result = gq.run("Show total revenue by month", return_result=True)

print(result.sql)
print(result.plan)
print(result.df)
```

## Use `generate()`

`GenQuery.generate(...)` also executes the full pipeline and returns a `QueryResult`:

```python generate.py
result = gq.generate("Show average order value by region")
print(result.sql)
print(result.df)
```

## What to read next

- [Async API](../usage/async-api.md)
- [Dry Run](../usage/dry-run.md)
- [Streaming](../usage/streaming.md)
- [Configuration](../usage/configuration.md)

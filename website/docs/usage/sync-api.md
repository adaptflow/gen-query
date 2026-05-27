---
title: Sync API
---

# Sync API

Use `GenQuery` in scripts, notebooks, jobs, and synchronous web applications.

## Basic usage

```python sync_api.py
from genquery import GenQuery
from genquery.adapters.openai_adapter import OpenAIAdapter

llm = OpenAIAdapter(api_key="sk-...", model="gpt-5.5")

gq = GenQuery(
    llm=llm,
    connection_string="sqlite:///app.db",
    schema="public",
)

df = gq.run("Count orders by status")
print(df)
```

## Return metadata

```python sync_metadata.py
result = gq.run("Count orders by status", return_result=True)

print(result.sql)
print(result.plan)
print(result.df)
```

## Related APIs

- Use `dry_run()` to inspect generated SQL without execution.
- Use `stream()` for large final result sets.
- Use `generate()` when you always want a `QueryResult`.

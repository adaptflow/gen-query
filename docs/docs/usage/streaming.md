---
title: Streaming
---

# Streaming Results

Use `stream()` when the final query result may be large.

Streaming is final-result-only: intermediate steps in multi-step plans are still materialized so later steps can use them as context, while the final step is yielded incrementally.

## Sync streaming

```python streaming.py
result = gq.stream("Show all orders from this year", batch_size=5000)

print(result.sql)

with result.stream as batches:
    for batch in batches:
        print(batch)
```

## Async streaming

```python async_streaming.py
from genquery import AsyncGenQuery
from genquery.adapters.openai_adapter import AsyncOpenAIAdapter

llm = AsyncOpenAIAdapter(api_key="sk-...", model="gpt-5.5")

async with AsyncGenQuery(
    llm=llm,
    connection_string="postgresql+asyncpg://user:pass@localhost:5432/mydb",
    schema="public",
) as gq:
    result = await gq.stream("Show all orders from this year", batch_size=5000)

    async with result.stream as batches:
        async for batch in batches:
            print(batch)
```

## Batch size and row limits

The stream yields Polars DataFrame batches and respects the configured `row_limit`. Configure the default batch size with `stream_batch_size`, or override it per call with `batch_size`.

:::warning
If you may stop iteration early, use the stream as a context manager so the database connection is closed promptly.
:::

Empty result sets yield one empty Polars DataFrame with the result columns.

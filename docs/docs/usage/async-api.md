---
title: Async API
---

# Async API

Use `AsyncGenQuery` in asyncio applications such as FastAPI, Starlette, aiohttp, workers, and background services.

## Basic async usage

```python async_api.py
import asyncio
from genquery import AsyncGenQuery
from genquery.adapters.openai_adapter import AsyncOpenAIAdapter

async def main():
    llm = AsyncOpenAIAdapter(api_key="sk-...", model="gpt-5-mini")

    async with AsyncGenQuery(
        llm=llm,
        connection_string="postgresql+asyncpg://user:pass@localhost:5432/mydb",
        schema="public",
    ) as gq:
        df = await gq.run("Show me the top 5 customers by total order amount this year")
        print(df)

asyncio.run(main())
```

## Return metadata

```python async_metadata.py
result = await gq.run("Show total revenue by month", return_result=True)

print(result.sql)
print(result.plan)
print(result.df)
```

## Generate a QueryResult

```python async_generate.py
result = await gq.generate("Show average order value by region")
print(result.sql)
print(result.df)
```

:::tip
Use an async SQLAlchemy URL, such as `postgresql+asyncpg://...` or `sqlite+aiosqlite:///app.db`, when using `AsyncGenQuery`.
:::

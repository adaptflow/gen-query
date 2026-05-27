---
title: FastAPI Example
---

# FastAPI Example

This example shows how to create a shared `AsyncGenQuery` instance for a FastAPI application.

```python fastapi_app.py
from fastapi import FastAPI
from genquery import AsyncGenQuery
from genquery.adapters.openai_adapter import AsyncOpenAIAdapter

app = FastAPI()

@app.on_event("startup")
async def startup():
    llm = AsyncOpenAIAdapter(api_key="sk-...", model="gpt-5-mini")
    app.state.gq = AsyncGenQuery(
        llm=llm,
        connection_string="postgresql+asyncpg://user:pass@localhost:5432/mydb",
        schema="public",
    )

@app.on_event("shutdown")
async def shutdown():
    await app.state.gq.close()

@app.post("/query")
async def query_database(payload: dict):
    result = await app.state.gq.run(payload["query"], return_result=True)
    return {
        "sql": result.sql,
        "rows": result.df.to_dicts() if result.df is not None else [],
    }
```

:::warning
For public APIs, validate and authorize user requests before sending them to GenQuery. Prefer read-only database credentials and configure row limits and statement timeouts.
:::

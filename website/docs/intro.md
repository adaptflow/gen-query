---
title: Introduction
sidebar_position: 1
---

# GenQuery

GenQuery is an agentic, highly customizable Natural Language to SQL generation and execution framework for Python. It converts natural-language questions into executable SQL, validates the SQL for safety, executes it against your database, and returns results as Polars DataFrames or streaming Polars batches.

## Why GenQuery?

- **Agentic pipeline**: The default pipeline is split into Inspector, Ranker, Planner, and Executor stages.
- **Sync and async APIs**: Use `GenQuery` in regular Python apps or `AsyncGenQuery` in asyncio services such as FastAPI, Starlette, and aiohttp.
- **Multi-LLM support**: Built-in adapters are available for OpenAI, Anthropic, Gemini, LangChain, and Ollama.
- **Security-first execution**: Generated SQL is validated as read-only and can be constrained with row limits, statement timeouts, and Row-Level Security policies.
- **Enterprise scale features**: Semantic table ranking, schema caching, execution plans, configurable row limits, and final-result streaming help keep large schemas manageable.
- **Customizable by design**: Replace pipeline stages, provide callbacks, and adapt GenQuery to your own environment.

## Basic flow

1. GenQuery inspects your database schema.
2. It ranks relevant tables for the user's natural-language request.
3. It creates a logical execution plan.
4. It generates, validates, and executes SQL.
5. It returns a Polars DataFrame or a stream of Polars batches.

## Start here

- Install GenQuery in [Installation](./getting-started/installation.md).
- Run your first query in [Quick Start](./getting-started/quick-start.md).
- Learn the command line in [CLI](./getting-started/cli.md).
- Review production safeguards in [Security](./security/overview.md).

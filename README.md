# GenQuery

[![PyPI version](https://img.shields.io/pypi/v/genquery.svg)](https://pypi.org/project/genquery/)
[![License](https://img.shields.io/github/license/adaptflow/gen-query.svg)](https://github.com/adaptflow/gen-query/blob/main/LICENSE)
[![Downloads](https://img.shields.io/badge/downloads-PyPI-blue.svg)](https://pypi.org/project/genquery/)

[![Documentation](https://img.shields.io/badge/docs-Read%20the%20full%20documentation-blue?style=for-the-badge)](https://adaptflow.github.io/gen-query/)

Read the full documentation, guides, and examples at **[adaptflow.github.io/gen-query](https://adaptflow.github.io/gen-query/)**.

GenQuery is an agentic, highly customizable Natural Language to SQL generation and execution framework. It converts natural language queries into executable SQL, validates security, executes the queries against your database, and returns results as Polars DataFrames or streaming Polars batches.

## Key Features

- **Agentic Pipeline**: Broken down into discrete, customizable stages: Inspector, Ranker, Planner, Executor.
- **Sync and Async APIs**: Use `GenQuery` in synchronous apps or `AsyncGenQuery` in asyncio-based web servers such as FastAPI, Starlette, and aiohttp.
- **Multi-LLM Support**: Built-in adapters for OpenAI, Anthropic, Gemini, LangChain, and Ollama local models.
- **Async LLM Support**: Async adapters are available for OpenAI, Anthropic, Gemini, LangChain, and Ollama.
- **Security-First**: Enforces strictly read-only (`SELECT`) queries via AST validation and injects Row-Level Security (RLS) policies dynamically.
- **Enterprise Scale**: Includes semantic table ranking to avoid context limits, execution plans for complex queries, schema caching, final-result streaming, configurable row limits, and statement timeouts.
- **Dry Run Mode**: Use `dry_run()` to safely generate SQL and execution plans without executing against the database. Perfect for debugging, review, or understanding how a query will be interpreted before running it.
- **Streaming Results**: Use `stream()` to consume large final query results as Polars DataFrame batches without materializing the full final result in memory. Both sync and async streaming are supported.
- **Command-Line Interface**: Run one-liners directly from your terminal with the `genquery` CLI entry point.
- **Configurable Logging**: Package logging defaults to `INFO` with minimal info-level output; switch to `DEBUG` for detailed diagnostics.
- **Customizable**: Swap out any pipeline stage to fit your specific needs or integrate with your own systems.


## Architecture

The system operates on a 4-stage pipeline by default:

1. **Schema Inspector**: Connects to the database via SQLAlchemy, extracts schema metadata, and caches it.
2. **Semantic Ranker**: Uses an LLM to identify and rank only the relevant tables for the user's query, reducing context overhead.
3. **Query Planner**: Breaks the natural language request down into a logical execution plan.
4. **Query Executor**: Generates SQL for each step in the plan, applies AST-based security limits and validations, executes the queries safely, and returns a Polars DataFrame or a final-result stream of Polars DataFrame batches.

Both synchronous and asynchronous pipeline implementations are available.

## Installation

Install GenQuery and the dependencies for your preferred LLM/database stack:

```bash
pip install genquery
```

For local development or manual dependency installation:

```bash
pip install sqlalchemy polars pydantic sqlglot pyyaml requests
# Plus your LLM provider of choice:
# pip install openai anthropic google-generativeai langchain
```

### Database Driver Extras

Install only the drivers you need for your database (both sync and async are included):

```bash
# PostgreSQL (psycopg2 + asyncpg)
pip install "genquery[postgres]"

# MySQL (mysqlclient + asyncmy)
pip install "genquery[mysql]"

# MSSQL (pymssql + aioodbc)
pip install "genquery[mssql]"

# Oracle (oracledb)
pip install "genquery[oracle]"

# SQLite (aiosqlite)
pip install "genquery[sqlite]"

# All database drivers
pip install "genquery[all]"
```

## Quick Start

```python
from genquery import GenQuery
from genquery.adapters.openai_adapter import OpenAIAdapter

# 1. Initialize your LLM adapter
llm = OpenAIAdapter(api_key="sk-...", model="gpt-5.5")

# 2. Setup GenQuery with individual parameters
gq = GenQuery(
    llm=llm,
    connection_string="postgresql://user:pass@localhost:5432/mydb",
    schema="public",
)

# 3. Run a query
df = gq.run("Show me the top 5 customers by total order amount this year")
print(df)
```

To receive SQL, plan, DataFrame, and updated conversation history:

```python
result = gq.run("Show total revenue by month", return_result=True)

print(result.sql)
print(result.plan)
print(result.df)
```

`GenQuery.generate(...)` also executes the full pipeline and returns a `QueryResult`:

```python
result = gq.generate("Show average order value by region")
print(result.sql)
print(result.df)
```

### Dry Run (Safe Inspection)

Use `dry_run()` to generate SQL and the execution plan **without executing against the database**:

```python
result = gq.dry_run("Show me the top 5 customers by total order amount this year")

print("Generated SQL:")
print(result.sql)

print("\nExecution Plan Steps:")
for step in result.steps:
    print(f"  - {step.description}")
```

The `dry_run()` method runs the full pipeline through schema inspection, table ranking, SQL generation, and security validation — then prefixes the generated SQL with `EXPLAIN` instead of executing it. The returned `QueryResult` contains the generated SQL, the execution plan, and the step-by-step plan details, but `df` and `stream` will be `None`. This is completely safe for debugging, reviewing generated SQL, or understanding how the system interprets a natural-language query before running it against live data.

## CLI Quick Start

GenQuery ships with a convenient command-line interface for quick experimentation. After installing the package, use the `genquery` command directly from your terminal:

```bash
# Basic usage (OpenAI API key defaults to OPENAI_API_KEY env var)
genquery "Count orders by status" --conn postgresql://user:pass@localhost:5432/mydb

# Specify a different model
genquery "List all orders this month" --conn sqlite:///app.db --model gpt-5.4 --api-key sk-...

# Use a YAML configuration file
genquery "Count users by role" --conn postgresql://user:pass@localhost:5432/mydb --config config.yaml

# Override the database schema
genquery "Find all transactions of this week" --conn postgresql://user:pass@localhost:5432/mydb --schema analytics

# Point to a custom OpenAI-compatible endpoint
genquery "Find recent orders" --conn sqlite:///app.db --base-url https://openrouter.ai/api/v1 --api-key dummy-key

# Enable detailed debug logs
genquery "Count orders by status" --conn sqlite:///app.db --log-level DEBUG
```


All arguments:
| Argument | Required | Default | Description |
|---|---|---|---|
| `query` | ✅ (positional) | — | Natural language query |
| `--conn` | ✅ | — | Database connection string |
| `--api-key` | ❌ | `OPENAI_API_KEY` env var | OpenAI API key |
| `--model` | ❌ | `gpt-5.5` | OpenAI model name |
| `--base-url` | ❌ | `https://api.openai.com/v1` | Base URL for the OpenAI-compatible API. Useful for local proxies, self-hosted models, or alternative providers. |
| `--schema` | ❌ | `public` | Database schema |
| `--config` | ❌ | `None` | Path to YAML config file |
| `--log-level` | ❌ | `INFO` | Log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`) |

For development, install the package in editable mode to test changes:

```bash
pip install -e .
genquery "Count orders by statuss" --conn sqlite:///app.db
```

## Async Quick Start

Use `AsyncGenQuery` in asyncio-based applications such as FastAPI.

```python
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

To receive SQL, plan, DataFrame, and updated conversation history:

```python
result = await gq.run("Show total revenue by month", return_result=True)

print(result.sql)
print(result.plan)
print(result.df)
```

`AsyncGenQuery.generate(...)` matches the sync `generate(...)` behavior and executes the full pipeline:

```python
result = await gq.generate("Show average order value by region")
print(result.sql)
print(result.df)
```

### Async Dry Run (Safe Inspection)

`AsyncGenQuery` also provides `dry_run()` for safe async inspection:

```python
result = await gq.dry_run("Show me the top 5 customers by total order amount this year")

print("Generated SQL:")
print(result.sql)

print("\nExecution Plan Steps:")
for step in result.steps:
    print(f"  - {step.description}")
```

The async `dry_run()` behaves identically to its sync counterpart — it generates SQL and an execution plan without executing against the database, returning a `QueryResult` with `sql`, `plan`, and `steps` populated, but `df` and `stream` set to `None`.

## Streaming Results

Use `stream()` when the final result may be large. Streaming is final-result-only: intermediate steps in multi-step plans are still materialized so later steps can use them as context, while the final step is yielded incrementally.

The stream yields Polars DataFrame batches and respects the configured `row_limit`. Configure the default batch size with `stream_batch_size`, or override it per call with `batch_size`.

```python
result = gq.stream("Show all orders from this year", batch_size=5000)

print(result.sql)

with result.stream as batches:
    for batch in batches:
        # batch is a Polars DataFrame
        print(batch)
```

Async streaming is also supported:

```python
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
            # batch is a Polars DataFrame
            print(batch)
```

Empty result sets yield one empty Polars DataFrame with the result columns. If you may stop iteration early, use the stream as a context manager so the database connection is closed promptly.

## FastAPI Example

```python
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

## Configuration

You can configure GenQuery via code or a YAML file to enforce table filters, row limits, stream batch sizes, statement timeouts, and Row-Level Security (RLS).

### Python Configuration

```python
from genquery import GenQuery
from genquery.config import GenQueryConfig, TableFilterConfig, RLSPolicy

config = GenQueryConfig(
    connection_string="postgresql://user:pass@localhost:5432/mydb",
    schema_name="public",
    connect_args={"connect_timeout": 10},
    table_filters=TableFilterConfig(exclude=["migrations", "audit_logs"]),
    statement_timeout_ms=10000,
    row_limit=100,
    stream_batch_size=10000,
    log_level="INFO",
    rls_policies=[RLSPolicy(column="tenant_id", value="t-12345")],
)

gq = GenQuery(llm=llm, config=config)

```

For async usage, use an async SQLAlchemy connection string:

```python
from genquery import AsyncGenQuery
from genquery.config import GenQueryConfig

config = GenQueryConfig(
    connection_string="postgresql+asyncpg://user:pass@localhost:5432/mydb",
    schema_name="public",
    row_limit=100,
    stream_batch_size=10000,
    log_level="INFO",
)

gq = AsyncGenQuery(llm=async_llm, config=config)

```

### YAML Configuration

```yaml
# config.yaml
connection_string: "postgresql://user:pass@localhost:5432/mydb"
schema_name: "public"
statement_timeout_ms: 10000
row_limit: 100
stream_batch_size: 10000
log_level: "INFO"
rls_policies:
  - column: "tenant_id"

    value: "t-12345"
table_filters:
  exclude: ["migrations", "audit_logs"]
```

```python
gq = GenQuery(llm=llm, config_path="config.yaml")
```

### Logging

Logging is configured through the package-level `genquery` logger. The default level is `INFO`, and info-level messages are intentionally minimal to avoid overhead/noise. Use `DEBUG` when troubleshooting pipeline stages, schema cache behavior, SQL generation retries, or execution failures.

You can set the level in code, configuration, or the CLI:

```python
from genquery import GenQuery, configure_logging

configure_logging("DEBUG")
gq = GenQuery(llm=llm, connection_string="sqlite:///app.db", log_level="DEBUG")
```

```yaml
log_level: "DEBUG"
```

```bash
genquery "Count orders" --conn sqlite:///app.db --log-level DEBUG
```

## Supported LLMs

GenQuery includes synchronous adapters for:


- `OpenAIAdapter`
- `AnthropicAdapter`
- `GeminiAdapter`
- `OllamaAdapter`
- `LangChainAdapter`

Async adapters are also available:

- `AsyncOpenAIAdapter`
- `AsyncAnthropicAdapter`
- `AsyncGeminiAdapter`
- `AsyncOllamaAdapter`
- `AsyncLangChainAdapter`

Example:

```python
from genquery.adapters.openai_adapter import OpenAIAdapter, AsyncOpenAIAdapter

sync_llm = OpenAIAdapter(api_key="sk-...", model="gpt-5-mini")
async_llm = AsyncOpenAIAdapter(api_key="sk-...", model="gpt-5-mini")
```

## Supported Databases

GenQuery uses SQLAlchemy for database connectivity.

### Sync Database URLs

Examples:

- PostgreSQL: `postgresql://user:pass@host:5432/db`
- SQLite: `sqlite:///app.db`
- MySQL: `mysql://user:pass@host:3306/db`
- MSSQL: `mssql+pymssql://user:pass@host:1433/db`
- Oracle: `oracle+oracledb://user:pass@host:1521/?service_name=service`

### Async Database URLs

Examples:

- PostgreSQL: `postgresql+asyncpg://user:pass@host:5432/db`
- SQLite: `sqlite+aiosqlite:///app.db`
- MySQL: `mysql+asyncmy://user:pass@host:3306/db`
- MSSQL: `mssql+aioodbc://user:pass@host:1433/db`
- Oracle: `oracle+oracledb://user:pass@host:1521/?service_name=service`

Async support depends on the installed SQLAlchemy-compatible async driver for each database.

## Security

### Read-Only Enforcement

All generated SQL is validated using AST parsing to ensure it contains only read-only statements. `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, and other destructive operations are rejected.

### Row Limits

Generated SQL is modified to enforce configured row limits where supported. Streaming results also respect `row_limit`.

### Row-Level Security

The executor can apply Row-Level Security policies in two ways:

- **AST injection**: Adds filter conditions to generated SQL.
- **Session variables**: Sets PostgreSQL session variables that trigger database-native RLS policies.

## Customizing the Pipeline

GenQuery's pipeline architecture makes it possible to replace any stage.

```python
from genquery import GenQuery
from genquery.pipeline.inspector.inspector import SchemaInspectorStage
from genquery.pipeline.state import PipelineStage, PipelineState

class MyCustomInspector(PipelineStage):
    def run(self, state: PipelineState) -> PipelineState:
        state.schema_context = custom_schema_object
        return state

gq = GenQuery(llm=my_llm_adapter, connection_string="...")

gq.pipeline.replace_stage(SchemaInspectorStage, MyCustomInspector())

result = gq.run("Find the average salary of all active employees")
```

## Customizing the Async Pipeline

Use `AsyncPipelineStage` for async custom stages.

```python
from genquery import AsyncGenQuery
from genquery.pipeline.inspector.inspector import AsyncSchemaInspectorStage
from genquery.pipeline.state import AsyncPipelineStage, PipelineState

class MyAsyncCustomInspector(AsyncPipelineStage):
    async def run(self, state: PipelineState) -> PipelineState:
        state.schema_context = await load_schema_context()
        return state

gq = AsyncGenQuery(llm=async_llm_adapter, connection_string="postgresql+asyncpg://...")

gq.pipeline.replace_stage(AsyncSchemaInspectorStage, MyAsyncCustomInspector())

result = await gq.run("Find the average salary of all active employees", return_result=True)
```

## Callbacks and Observability

Track pipeline execution at every step using `GenQueryCallbackHandler`:

```python
from genquery.core.callbacks import GenQueryCallbackHandler

class MyLogger(GenQueryCallbackHandler):
    def on_sql_generated(self, step_id: str, sql: str) -> None:
        print(f"Generated SQL for {step_id}: {sql}")

gq = GenQuery(llm=llm, connection_string="...", callbacks=MyLogger())
```

## Async Callbacks

Use `AsyncGenQueryCallbackHandler` for async pipelines.

Async callbacks are additive to sync callbacks. The default async methods call the corresponding sync methods, so you can override sync methods for lightweight logging or override async methods for non-blocking work.

```python
from genquery import AsyncGenQuery
from genquery.core.callbacks import AsyncGenQueryCallbackHandler

class MyAsyncLogger(AsyncGenQueryCallbackHandler):
    async def aon_sql_generated(self, step_id: str, sql: str) -> None:
        await write_log_async(f"Generated SQL for {step_id}: {sql}")

gq = AsyncGenQuery(
    llm=async_llm,
    connection_string="postgresql+asyncpg://...",
    callbacks=MyAsyncLogger(),
)
```

For lightweight sync-style logging in async pipelines:

```python
from genquery.core.callbacks import AsyncGenQueryCallbackHandler

class MyLogger(AsyncGenQueryCallbackHandler):
    def on_sql_generated(self, step_id: str, sql: str) -> None:
        print(f"Generated SQL for {step_id}: {sql}")
```
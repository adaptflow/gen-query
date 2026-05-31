---
title: Installation
---

# Installation

Install GenQuery from PyPI:

```bash terminal
pip install genquery
```

## Optional feature dependencies

`pip install genquery` installs the core package dependencies and the OpenAI adapter dependency. Some adapters and features import provider-specific packages only when you use them, so install the packages for the features you need:

| Feature | Install when needed |
|---|---|
| YAML configuration files (`config_path` / `GenQueryConfig.from_yaml`) | `pip install pyyaml` |
| Anthropic adapters | `pip install anthropic` |
| Gemini adapters | `pip install google-generativeai` |
| LangChain adapters | `pip install langchain langchain-core` |
| Ollama adapters | `pip install requests` |

## Manual dependency installation

If you are installing dependencies manually for local development, install the core dependencies and your preferred LLM provider package:

```bash terminal
pip install sqlalchemy polars pydantic sqlglot pyyaml requests openai
pip install anthropic google-generativeai langchain langchain-core
```

## Database driver extras

Install only the database drivers you need. GenQuery extras include both sync and async drivers where applicable.

```bash terminal
# PostgreSQL: psycopg2 + asyncpg
pip install "genquery[postgres]"

# MySQL: mysqlclient + asyncmy
pip install "genquery[mysql]"

# MSSQL: pymssql + aioodbc
pip install "genquery[mssql]"

# Oracle: oracledb
pip install "genquery[oracle]"

# SQLite: aiosqlite
pip install "genquery[sqlite]"

# All database drivers
pip install "genquery[all]"
```

## Development install

From a local checkout:

```bash terminal
pip install -e .
genquery "Count orders by status" --conn sqlite:///app.db
```

## Next step

Continue to the [Quick Start](./quick-start.md).

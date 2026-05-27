---
title: Installation
---

# Installation

Install GenQuery from PyPI:

```bash terminal
pip install genquery
```

## Manual dependency installation

If you are installing dependencies manually for local development, install the core dependencies and your preferred LLM provider package:

```bash terminal
pip install sqlalchemy polars pydantic sqlglot pyyaml requests
pip install openai anthropic google-generativeai langchain
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

---
title: Supported Databases
---

# Supported Databases

GenQuery uses SQLAlchemy for database connectivity. Install the SQLAlchemy-compatible driver for your database before connecting.

## Sync database URLs

- PostgreSQL: `postgresql://user:pass@host:5432/db`
- SQLite: `sqlite:///app.db`
- MySQL: `mysql://user:pass@host:3306/db`
- MSSQL: `mssql+pymssql://user:pass@host:1433/db`
- Oracle: `oracle+oracledb://user:pass@host:1521/?service_name=service`

## Async database URLs

- PostgreSQL: `postgresql+asyncpg://user:pass@host:5432/db`
- SQLite: `sqlite+aiosqlite:///app.db`
- MySQL: `mysql+asyncmy://user:pass@host:3306/db`
- MSSQL: `mssql+aioodbc://user:pass@host:1433/db`
- Oracle: `oracle+oracledb://user:pass@host:1521/?service_name=service`

Async support depends on the installed SQLAlchemy-compatible async driver for each database.

## Driver extras

```bash terminal
pip install "genquery[postgres]"
pip install "genquery[mysql]"
pip install "genquery[mssql]"
pip install "genquery[oracle]"
pip install "genquery[sqlite]"
pip install "genquery[all]"
```

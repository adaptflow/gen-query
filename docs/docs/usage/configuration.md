---
title: Configuration
---

# Configuration

You can configure GenQuery through constructor parameters, a `GenQueryConfig` object, or a YAML file.

Configuration controls database connection behavior, table filters, row limits, stream batch sizes, statement timeouts, logging, and Row-Level Security policies.

## Python configuration

```python configuration.py
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

## Async configuration

```python async_configuration.py
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

## YAML configuration

```yaml config.yaml
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

Load the YAML configuration file:

```python load_config.py
gq = GenQuery(llm=llm, config_path="config.yaml")
```

## Important options

| Option | Description |
|---|---|
| `connection_string` | SQLAlchemy database URL. |
| `schema_name` | Database schema to inspect. |
| `connect_args` | Driver-specific connection arguments. |
| `table_filters` | Include or exclude tables from schema inspection. |
| `statement_timeout_ms` | Maximum statement execution time where supported. |
| `row_limit` | Maximum number of rows returned. |
| `stream_batch_size` | Default batch size for streaming. |
| `log_level` | Package log level. |
| `rls_policies` | Row-Level Security policies to apply. |

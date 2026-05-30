---
title: Configuration API
---

# Configuration API

Configuration models are Pydantic models in `genquery.config`.

## Imports

```python imports.py
from genquery.config import GenQueryConfig, TableFilterConfig, RLSPolicy, PromptsConfig
```

## `GenQueryConfig`

Main configuration model for GenQuery.

```python signature.py
GenQueryConfig(
    connection_string,
    schema_name="public",
    connect_args={},
    table_filters=TableFilterConfig(),
    prompts=PromptsConfig(),
    rls_policies=[],
    statement_timeout_ms=15000,
    schema_cache_ttl_seconds=3600,
    schema_cache_dir=".gq_cache",
    row_limit=1000,
    stream_batch_size=10000,
    log_level="INFO",
)
```

### Fields

| Field | Type | Default | Description |
|---|---|---|---|
| `connection_string` | `str` | Required | SQLAlchemy database URL. |
| `schema_name` | `str` | `"public"` | Schema used for inspection and generated SQL context. |
| `connect_args` | `dict[str, Any]` | `{}` | Extra arguments for SQLAlchemy engine creation. |
| `table_filters` | `TableFilterConfig` | `TableFilterConfig()` | Include/exclude rules for inspected tables. |
| `prompts` | `PromptsConfig` | `PromptsConfig()` | Optional custom prompt file paths. |
| `rls_policies` | `list[RLSPolicy]` | `[]` | Row-Level Security policies. |
| `statement_timeout_ms` | `int` | `15000` | Statement timeout in milliseconds where supported. |
| `schema_cache_ttl_seconds` | `int` | `3600` | Schema cache time-to-live. |
| `schema_cache_dir` | `str` | `.gq_cache` | Directory for schema cache files. |
| `row_limit` | `int` | `1000` | Maximum rows to return. |
| `stream_batch_size` | `int` | `10000` | Default streaming batch size. |
| `log_level` | `str \| int` | `"INFO"` | Package logging level. |

### Example

```python config_example.py
from genquery.config import GenQueryConfig, TableFilterConfig, RLSPolicy

config = GenQueryConfig(
    connection_string="postgresql://user:pass@localhost:5432/mydb",
    schema_name="public",
    table_filters=TableFilterConfig(exclude=["migrations", "audit_logs"]),
    rls_policies=[RLSPolicy(column="tenant_id", value="tenant-123")],
    row_limit=500,
    statement_timeout_ms=10000,
)
```

### `from_yaml()`

```python signature.py
GenQueryConfig.from_yaml(path, connection_string=None, schema_name=None, connect_args=None)
```

Loads configuration from a YAML file. Optional arguments override or merge into the YAML values.

```python from_yaml.py
config = GenQueryConfig.from_yaml(
    "config.yaml",
    connection_string="postgresql://user:pass@localhost:5432/mydb",
    schema_name="analytics",
)
```

Raises:

- `FileNotFoundError` if the path does not exist.
- `ValueError` if no `connection_string` is provided in the file or as an override.

## `TableFilterConfig`

Controls which tables are included in schema context.

```python signature.py
TableFilterConfig(
    include=None,
    exclude=None,
    regex=None,
    prefix=None,
    suffix=None,
)
```

| Field | Type | Description |
|---|---|---|
| `include` | `list[str] \| None` | Explicit tables to include. |
| `exclude` | `list[str] \| None` | Tables to exclude. |
| `regex` | `Pattern \| str \| None` | Regex pattern used to include matching tables. |
| `prefix` | `str \| None` | Include tables with this prefix. |
| `suffix` | `str \| None` | Include tables with this suffix. |

```python table_filters.py
filters = TableFilterConfig(
    exclude=["migrations", "audit_logs"],
    prefix="analytics_",
)
```

## `RLSPolicy`

Defines a Row-Level Security policy.

```python signature.py
RLSPolicy(column, value, session_variable=None)
```

| Field | Type | Description |
|---|---|---|
| `column` | `str` | Column to filter on, such as `tenant_id`. |
| `value` | `str` | Required value for the RLS condition. |
| `session_variable` | `str \| None` | Optional database session variable for native RLS policies. |

```python rls_policy.py
policy = RLSPolicy(column="tenant_id", value="tenant-123")
```

## `PromptsConfig`

Stores optional prompt file paths.

```python signature.py
PromptsConfig(
    ranker_prompt_path=None,
    planner_prompt_path=None,
    generator_prompt_path=None,
)
```

| Field | Description |
|---|---|
| `ranker_prompt_path` | Custom semantic ranking prompt path. |
| `planner_prompt_path` | Custom query planning prompt path. |
| `generator_prompt_path` | Custom SQL generation prompt path. |

### `load_prompt()`

```python signature.py
prompts.load_prompt(path_attr, default_prompt)
```

Loads the file named by `path_attr` when set and present; otherwise returns `default_prompt`.

## Related pages

- [GenQuery](./genquery.md)
- [AsyncGenQuery](./async-genquery.md)
- [Security Overview](../security/overview.md)

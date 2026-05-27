---
title: Models
---

# Models

GenQuery uses Pydantic models for conversation context, schema metadata, and query planning.

## Imports

```python imports.py
from genquery.core.models import (
    ConversationTurn,
    ConversationContext,
    ColumnMetadata,
    IndexMetadata,
    TableMetadata,
    SchemaContext,
    PlanStep,
    QueryPlan,
)
```

## Conversation models

### `ConversationTurn`

A prior natural-language query and its generated artifacts.

```python signature.py
ConversationTurn(
    user_query,
    sql=None,
    plan=None,
    result_summary=None,
)
```

| Field | Type | Description |
|---|---|---|
| `user_query` | `str` | Prior user request. |
| `sql` | `str \| None` | SQL generated for that turn. |
| `plan` | `dict[str, Any] \| None` | Plan metadata for that turn. |
| `result_summary` | `str \| None` | Short summary of results. |

```python conversation_turn.py
turn = ConversationTurn(
    user_query="Show revenue by month",
    sql="SELECT ...",
    result_summary="Returned 12 monthly rows",
)
```

### `ConversationContext`

Portable conversation history.

```python signature.py
ConversationContext(turns=[])
```

#### `format_for_prompt()`

```python signature.py
context.format_for_prompt(max_turns=3)
```

Renders recent conversation turns into text for prompts.

## Schema metadata models

### `ColumnMetadata`

```python signature.py
ColumnMetadata(name, type, primary_key, nullable)
```

| Field | Type |
|---|---|
| `name` | `str` |
| `type` | `str` |
| `primary_key` | `bool` |
| `nullable` | `bool` |

### `IndexMetadata`

```python signature.py
IndexMetadata(name, column_names, unique)
```

| Field | Type |
|---|---|
| `name` | `str` |
| `column_names` | `list[str]` |
| `unique` | `bool` |

### `TableMetadata`

```python signature.py
TableMetadata(
    name,
    description=None,
    columns,
    foreign_keys=[],
    indexes=[],
)
```

| Field | Type | Description |
|---|---|---|
| `name` | `str` | Table name. |
| `description` | `str \| None` | Optional table comment or description. |
| `columns` | `list[ColumnMetadata]` | Table columns. |
| `foreign_keys` | `list[dict[str, Any]]` | Foreign key metadata from SQLAlchemy. |
| `indexes` | `list[IndexMetadata]` | Table indexes. |

### `SchemaContext`

```python signature.py
SchemaContext(tables, dialect)
```

| Field | Type | Description |
|---|---|---|
| `tables` | `list[TableMetadata]` | Tables available to the pipeline. |
| `dialect` | `str` | SQL dialect name. |

## Query plan models

### `PlanStep`

```python signature.py
PlanStep(
    id,
    description,
    depends_on=[],
    output_alias=None,
    receives_context=None,
)
```

| Field | Type | Description |
|---|---|---|
| `id` | `str` | Stable step identifier. |
| `description` | `str` | Natural-language description of the step. |
| `depends_on` | `list[str]` | IDs of prerequisite steps. |
| `output_alias` | `str \| None` | Optional alias for step output. |
| `receives_context` | `str \| None` | Optional previous result context. |

### `QueryPlan`

```python signature.py
QueryPlan(strategy, steps)
```

| Field | Type | Description |
|---|---|---|
| `strategy` | `str` | Plan strategy, typically `single`, `sequential`, or `parallel`. |
| `steps` | `list[PlanStep]` | Ordered plan steps. |

## Related pages

- [QueryResult](./query-result.md)
- [Pipeline](./pipeline.md)

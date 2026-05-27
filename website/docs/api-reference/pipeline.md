---
title: Pipeline API
---

# Pipeline API

The pipeline API is useful when you need custom stages, custom orchestration, or deep observability.

## Imports

```python imports.py
from genquery.pipeline.state import PipelineState, PipelineStage, AsyncPipelineStage
from genquery.pipeline.pipeline import GenQueryPipeline, AsyncGenQueryPipeline
```

## `PipelineState`

Holds mutable state as a request moves through the pipeline.

```python signature.py
PipelineState(
    query,
    schema_context=None,
    ranked_schema=None,
    plan=None,
    sql=None,
    df=None,
    stream=None,
    conversation=[],
    context={},
)
```

| Field | Type | Description |
|---|---|---|
| `query` | `str` | Current natural-language query. |
| `schema_context` | `SchemaContext \| None` | Full inspected schema. |
| `ranked_schema` | `SchemaContext \| None` | Schema after semantic table ranking. |
| `plan` | `QueryPlan \| None` | Generated execution plan. |
| `sql` | `str \| None` | Final SQL. |
| `df` | `Any \| None` | Final DataFrame for non-streaming execution. |
| `stream` | `Any \| None` | Final-result stream. |
| `conversation` | `list[ConversationTurn]` | Conversation history. |
| `context` | `dict[str, Any]` | Extra data passed between custom stages. |

## `PipelineStage`

Base class for synchronous custom stages.

```python signature.py
class PipelineStage:
    def run(self, state: PipelineState) -> PipelineState:
        ...
```

```python custom_stage.py
from genquery.pipeline.state import PipelineStage, PipelineState

class MyStage(PipelineStage):
    def run(self, state: PipelineState) -> PipelineState:
        state.context["my_stage_ran"] = True
        return state
```

## `AsyncPipelineStage`

Base class for asynchronous custom stages.

```python signature.py
class AsyncPipelineStage:
    async def run(self, state: PipelineState) -> PipelineState:
        ...
```

```python async_custom_stage.py
from genquery.pipeline.state import AsyncPipelineStage, PipelineState

class MyAsyncStage(AsyncPipelineStage):
    async def run(self, state: PipelineState) -> PipelineState:
        state.context["my_stage_ran"] = True
        return state
```

## `GenQueryPipeline`

Synchronous pipeline. Executes stages sequentially.

```python signature.py
GenQueryPipeline(stages=None)
```

### Methods

| Method | Description |
|---|---|
| `add_stage(stage)` | Append a stage to the pipeline. |
| `replace_stage(target_class, new_stage)` | Replace the first stage matching `target_class`. Returns `bool`. |
| `remove_stage(target_class)` | Remove the first stage matching `target_class`. Returns `bool`. |
| `execute(state)` | Run all stages and return `QueryResult`. |

## `AsyncGenQueryPipeline`

Asynchronous pipeline. Executes async stages sequentially.

```python signature.py
AsyncGenQueryPipeline(stages=None)
```

### Methods

| Method | Description |
|---|---|
| `add_stage(stage)` | Append an async stage to the pipeline. |
| `replace_stage(target_class, new_stage)` | Replace the first stage matching `target_class`. Returns `bool`. |
| `remove_stage(target_class)` | Remove the first stage matching `target_class`. Returns `bool`. |
| `execute(state)` | Await all stages and return `QueryResult`. |

## Default pipeline stages

The default synchronous pipeline uses:

```python sync_default_stages.py
from genquery.pipeline.inspector.inspector import SchemaInspectorStage
from genquery.pipeline.ranker.ranker import SemanticRankerStage
from genquery.pipeline.planner.planner import QueryPlannerStage
from genquery.pipeline.executor.executor import QueryExecutorStage
```

The default asynchronous pipeline uses:

```python async_default_stages.py
from genquery.pipeline.inspector.inspector import AsyncSchemaInspectorStage
from genquery.pipeline.ranker.ranker import AsyncSemanticRankerStage
from genquery.pipeline.planner.planner import AsyncQueryPlannerStage
from genquery.pipeline.executor.executor import AsyncQueryExecutorStage
```

## Replacing a stage

```python replace_stage.py
from genquery.pipeline.inspector.inspector import SchemaInspectorStage

gq.pipeline.replace_stage(SchemaInspectorStage, MyCustomInspector())
```

## Related pages

- [Custom Pipeline Stages](../customization/custom-pipeline-stages.md)
- [Models](./models.md)
- [QueryResult](./query-result.md)

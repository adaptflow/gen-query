---
title: Custom Pipeline Stages
---

# Custom Pipeline Stages

GenQuery's pipeline architecture makes it possible to replace any stage.

## Sync custom inspector

```python custom_inspector.py
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

## Async custom inspector

```python async_custom_inspector.py
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

## Common use cases

- Load schema metadata from a catalog instead of live inspection.
- Add domain-specific validation rules.
- Add organization-specific ranking or planning logic.
- Integrate with internal observability systems.

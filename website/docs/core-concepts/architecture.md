---
title: Architecture
---

# Architecture

GenQuery runs a four-stage pipeline by default. Each stage has a focused responsibility and can be customized or replaced.

## Default stages

1. **Schema Inspector**: Connects to the database through SQLAlchemy, extracts schema metadata, and caches it.
2. **Semantic Ranker**: Uses an LLM to identify and rank tables relevant to the user's query, reducing prompt size for large schemas.
3. **Query Planner**: Converts the natural-language request into a logical execution plan.
4. **Query Executor**: Generates SQL for each plan step, validates and constrains the SQL, executes it safely, and returns the final result.

Both synchronous and asynchronous pipeline implementations are available.

## Data flow

```text pipeline.txt
User question
  -> Schema inspection
  -> Relevant table ranking
  -> Execution plan generation
  -> SQL generation and validation
  -> Database execution
  -> Polars DataFrame or stream
```

## Related pages

- [Pipeline](./pipeline.md)
- [QueryResult](./query-result.md)
- [Custom Pipeline Stages](../customization/custom-pipeline-stages.md)

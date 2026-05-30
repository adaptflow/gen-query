---
title: Pipeline
---

# Pipeline

The pipeline is the orchestration layer that moves a request from natural language to validated SQL execution.

## Why a pipeline?

A staged pipeline makes GenQuery easier to understand, inspect, and customize. Instead of one black-box prompt, GenQuery separates schema discovery, relevance ranking, planning, and execution.

## Customization points

You can replace stages when you need custom behavior, such as:

- Loading schema context from an internal catalog.
- Applying custom table ranking.
- Adding organization-specific planning rules.
- Enforcing stricter SQL validation before execution.

See [Custom Pipeline Stages](../customization/custom-pipeline-stages.md) for examples.

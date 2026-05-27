---
title: CLI
---

# CLI

GenQuery ships with a `genquery` command for quick experimentation from your terminal.

## Basic usage

```bash terminal
# OpenAI API key defaults to the OPENAI_API_KEY environment variable
genquery "Count orders by status" --conn postgresql://user:pass@localhost:5432/mydb
```

## Common examples

```bash terminal
# Specify a model and API key
genquery "List all orders this month" --conn sqlite:///app.db --model gpt-5.4 --api-key sk-...

# Use a YAML configuration file
genquery "Count users by role" --conn postgresql://user:pass@localhost:5432/mydb --config config.yaml

# Override the database schema
genquery "Find all transactions of this week" --conn postgresql://user:pass@localhost:5432/mydb --schema analytics

# Use an OpenAI-compatible endpoint
genquery "Find recent orders" --conn sqlite:///app.db --base-url https://openrouter.ai/api/v1 --api-key dummy-key

# Enable debug logs
genquery "Count orders by status" --conn sqlite:///app.db --log-level DEBUG
```

## Arguments

| Argument | Required | Default | Description |
|---|---:|---|---|
| `query` | Yes | — | Natural-language query. |
| `--conn` | Yes | — | Database connection string. |
| `--api-key` | No | `OPENAI_API_KEY` | OpenAI API key. |
| `--model` | No | `gpt-5.5` | OpenAI model name. |
| `--base-url` | No | `https://api.openai.com/v1` | OpenAI-compatible API base URL. |
| `--schema` | No | `public` | Database schema. |
| `--config` | No | `None` | Path to YAML config file. |
| `--log-level` | No | `INFO` | Log level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`. |

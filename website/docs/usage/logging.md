---
title: Logging
---

# Logging

Logging is configured through the package-level `genquery` logger. The default level is `INFO`, and info-level messages are intentionally minimal.

Use `DEBUG` when troubleshooting pipeline stages, schema cache behavior, SQL generation retries, or execution failures.

## Configure in code

```python logging_config.py
from genquery import GenQuery, configure_logging

configure_logging("DEBUG")
gq = GenQuery(llm=llm, connection_string="sqlite:///app.db", log_level="DEBUG")
```

## Configure in YAML

```yaml config.yaml
log_level: "DEBUG"
```

## Configure in CLI

```bash terminal
genquery "Count orders" --conn sqlite:///app.db --log-level DEBUG
```

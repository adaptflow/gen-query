---
title: Logging API
---

# Logging API

GenQuery uses a dedicated package logger named `genquery`.

## Imports

```python imports.py
from genquery import configure_logging
from genquery.logging import normalize_log_level, get_logger
```

## `configure_logging()`

```python signature.py
configure_logging(level="INFO")
```

Configures and returns the package logger. Repeated calls update the level without adding duplicate handlers.

```python configure_logging.py
from genquery import configure_logging

logger = configure_logging("DEBUG")
```

Valid string levels:

- `DEBUG`
- `INFO`
- `WARNING`
- `WARN`
- `ERROR`
- `CRITICAL`

You may also pass an integer logging level.

## `normalize_log_level()`

```python signature.py
normalize_log_level(level)
```

Converts a string or integer log level to a standard Python logging level number.

```python normalize.py
from genquery.logging import normalize_log_level

level = normalize_log_level("DEBUG")
```

Raises `ValueError` for invalid string levels.

## `get_logger()`

```python signature.py
get_logger(name)
```

Returns a logger object for a given name.

```python get_logger.py
from genquery.logging import get_logger

logger = get_logger(__name__)
logger.debug("debug message")
```

:::note
The implementation returns `logging.getLogger(name)`. Public GenQuery modules pass their module names to this helper.
:::

## Configuration integration

You can also set logging through `GenQueryConfig`, constructor `log_level`, or the CLI.

```python config_logging.py
gq = GenQuery(llm=llm, connection_string="sqlite:///app.db", log_level="DEBUG")
```

```yaml config.yaml
log_level: "DEBUG"
```

```bash terminal
genquery "Count orders" --conn sqlite:///app.db --log-level DEBUG
```

## Related pages

- [Logging guide](../usage/logging.md)
- [Configuration API](./configuration.md)

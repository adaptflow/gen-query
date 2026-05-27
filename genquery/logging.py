import logging
import sys
from typing import Union


DEFAULT_LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
_LOGGER_NAME = "genquery"


def normalize_log_level(level: Union[str, int]) -> int:
    """Normalize a string or integer log level to a logging level number."""
    if isinstance(level, int):
        return level

    normalized = str(level).strip().upper()
    if normalized == "WARN":
        normalized = "WARNING"

    level_number = logging.getLevelName(normalized)
    if isinstance(level_number, int):
        return level_number

    raise ValueError(
        f"Invalid log level '{level}'. Use DEBUG, INFO, WARNING, ERROR, or CRITICAL."
    )


def configure_logging(level: Union[str, int] = "INFO") -> logging.Logger:
    """
    Configure and return the package logger.

    The package uses a dedicated ``genquery`` logger so callers can change log
    verbosity without modifying the root logger. Repeated calls update the log
    level without adding duplicate handlers.
    """
    logger = logging.getLogger(_LOGGER_NAME)
    logger.setLevel(normalize_log_level(level))
    logger.propagate = False

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter(DEFAULT_LOG_FORMAT))
        logger.addHandler(handler)

    logger.debug("GenQuery logging configured", extra={"log_level": logging.getLevelName(logger.level)})
    return logger


def get_logger(name: str) -> logging.Logger:
    """Return a logger under the GenQuery namespace."""
    return logging.getLogger(name)

from typing import Any

def get_dialect(engine: Any) -> str:
    name = engine.dialect.name
    if name == "postgresql":
        return "postgres"
    return name
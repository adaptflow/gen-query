from typing import Any

def get_dialect(engine: Any) -> str:
    """
    Get the dialect name from an SQLAlchemy engine.
    
    Args:
        engine: The SQLAlchemy engine.
        
    Returns:
        The normalized dialect name as a string.
    """
    name = engine.dialect.name
    if name == "postgresql":
        return "postgres"
    return name
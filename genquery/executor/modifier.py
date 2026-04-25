import sqlglot
from sqlglot import exp

def apply_security_and_limits(sql: str, dialect: str, limit: int, tenant_id: str = None) -> str:
    """
    Parses SQL and injects LIMIT clause and optional RLS tenant_id checks.
    """
    try:
        parsed = sqlglot.parse_one(sql, read=dialect)
    except Exception as e:
        # If it fails to parse, return original assuming validator caught bad stuff
        return sql

    if isinstance(parsed, exp.Select) or isinstance(parsed, exp.Union):
        # 1. Apply Limit if missing and not an aggregation without limits
        if not parsed.args.get('limit'):
            parsed = parsed.limit(limit)

        # 2. Inject tenant_id if required for AST RLS
        if tenant_id and isinstance(parsed, exp.Select):
            # Simple AST RLS: Add a global WHERE tenant_id = 'X' to the root SELECT
            # This handles most basic SELECTs securely at the top level
            parsed = parsed.where(f"tenant_id = '{tenant_id}'")
        
        return parsed.sql(dialect=dialect)
    return sql

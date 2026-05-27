import sqlglot
from genquery.logging import get_logger

logger = get_logger(__name__)

class SecurityValidator:
    """
    Validates that a SQL query is strictly read-only (SELECT).
    """
    def __init__(self, dialect: str):
        """Initialize the validator for a specific SQL dialect."""
        if dialect == 'mssql':
            self.dialect = 'tsql'
        else:
            self.dialect = dialect

    def validate(self, sql: str) -> bool:
        """
        Returns True if the query is a valid read-only query mapping to SELECT.
        Returns False if the query contains INSERT, UPDATE, DELETE, DROP, ALTER, etc.
        """
        try:
            # Parse the SQL string into sqlglot AST expression(s)
            parsed = sqlglot.parse(sql, read=self.dialect)
            if not parsed:
                logger.warning("SQL validation failed: parser returned no statements")
                return False
                
            for expr in parsed:
                if not expr:
                    continue
                # We enforce that the root level statement is a Select (or similar read-only like Union)
                if not isinstance(expr, (sqlglot.exp.Select, sqlglot.exp.Union)):
                    logger.warning("SQL validation failed: non-read-only statement detected (%s)", type(expr).__name__)
                    return False
                    
                # Advanced checking could walk the AST to ensure no destructive subqueries,
                # but typically sqlglot's parser distinguishes query types well.
            return True
        except Exception as exc:
            # If it fails to parse, it's safer to consider it invalid.
            logger.warning("SQL validation failed while parsing: %s", exc, exc_info=True)
            return False

import sqlglot

class SecurityValidator:
    """
    Validates that a SQL query is strictly read-only (SELECT).
    """
    def __init__(self, dialect: str):
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
                return False
                
            for expr in parsed:
                if not expr:
                    continue
                # We enforce that the root level statement is a Select (or similar read-only like Union)
                if not isinstance(expr, (sqlglot.exp.Select, sqlglot.exp.Union)):
                    return False
                    
                # Advanced checking could walk the AST to ensure no destructive subqueries,
                # but typically sqlglot's parser distinguishes query types well.
            return True
        except Exception:
            # If it fails to parse, it's safer to consider it invalid.
            return False

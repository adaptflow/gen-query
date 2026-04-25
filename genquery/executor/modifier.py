import sqlglot
from sqlglot import exp

def apply_security_and_limits(sql: str, dialect: str, limit: int, rls_policies: list = None, schema=None) -> str:
    """
    Parses SQL and injects LIMIT clause and optional dynamic RLS policies via AST replacement.
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

        # 2. Inject RLS policies if required via AST replacement
        if rls_policies:
            for table in list(parsed.find_all(exp.Table)):
                # Skip CTE definitions, we only want to replace references
                if isinstance(table.parent, exp.CTE):
                    continue
                    
                table_name = table.name
                alias = table.alias or table_name
                
                applicable_policies = []
                if schema:
                    # check if the table has the policy column
                    table_meta = next((t for t in schema.tables if t.name == table_name), None)
                    if table_meta:
                        columns = {c.name for c in table_meta.columns}
                        applicable_policies = [p for p in rls_policies if p.column in columns]
                else:
                    # If no schema, assume all policies apply
                    applicable_policies = rls_policies
                
                if applicable_policies:
                    conditions = [f"{p.column} = '{p.value}'" for p in applicable_policies]
                    where_sql = " AND ".join(conditions)
                    
                    sub_sql = f"SELECT * FROM {table_name} WHERE {where_sql}"
                    try:
                        sub_ast = sqlglot.parse_one(sub_sql, read=dialect)
                        sub_ast = sub_ast.subquery(alias)
                        table.replace(sub_ast)
                    except Exception:
                        pass
        
        return parsed.sql(dialect=dialect)
    return sql

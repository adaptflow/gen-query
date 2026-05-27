---
title: Security Overview
---

# Security Overview

GenQuery is designed for read-oriented analytics workflows. It validates generated SQL and provides controls for row limits, statement timeouts, and Row-Level Security policies.

:::warning
Use a read-only database user in production even though GenQuery validates generated SQL. Application-level validation should complement, not replace, database permissions.
:::

## Read-only enforcement

All generated SQL is validated using AST parsing to ensure it contains only read-only statements. Destructive operations such as `INSERT`, `UPDATE`, `DELETE`, `DROP`, and `ALTER` are rejected.

## Row limits

Generated SQL is modified to enforce configured row limits where supported. Streaming results also respect `row_limit`.

## Row-Level Security

The executor can apply Row-Level Security policies in two ways:

- **AST injection**: Adds filter conditions to generated SQL.
- **Session variables**: Sets PostgreSQL session variables that trigger database-native RLS policies.

## Production checklist

- Use least-privilege, read-only database credentials.
- Configure `row_limit` and `statement_timeout_ms`.
- Exclude sensitive tables with table filters.
- Review generated SQL for high-risk workflows with `dry_run()`.
- Avoid exposing unrestricted natural-language querying to untrusted users.

import polars as pl

from genquery.config import GenQueryConfig, RLSPolicy
from genquery.core.models import ColumnMetadata, PlanStep, SchemaContext, TableMetadata
from genquery.pipeline.executor.executor import (
    build_async_timeout_statement,
    build_generator_prompt,
    build_timeout_statement,
    clean_generated_sql,
    summarize_result,
)
from genquery.pipeline.executor.modifier import apply_security_and_limits
from genquery.pipeline.executor.validator import SecurityValidator


def schema_with_tenant_column() -> SchemaContext:
    return SchemaContext(
        dialect="sqlite",
        tables=[
            TableMetadata(
                name="items",
                columns=[
                    ColumnMetadata(name="id", type="INTEGER", primary_key=True, nullable=False),
                    ColumnMetadata(name="tenant_id", type="TEXT", primary_key=False, nullable=True),
                    ColumnMetadata(name="name", type="TEXT", primary_key=False, nullable=True),
                ],
            )
        ],
    )


def test_security_validator_allows_select_and_union_queries():
    validator = SecurityValidator("sqlite")

    assert validator.validate("SELECT 1") is True
    assert validator.validate("SELECT 1 UNION SELECT 2") is True


def test_security_validator_rejects_mutating_and_multi_statement_queries():
    validator = SecurityValidator("sqlite")

    assert validator.validate("INSERT INTO users (id) VALUES (1)") is False
    assert validator.validate("UPDATE users SET name = 'new'") is False
    assert validator.validate("DELETE FROM users") is False
    assert validator.validate("DROP TABLE users") is False
    assert validator.validate("SELECT 1; DROP TABLE users") is False


def test_security_validator_maps_mssql_to_tsql_dialect():
    validator = SecurityValidator("mssql")

    assert validator.dialect == "tsql"
    assert validator.validate("SELECT TOP 1 * FROM users") is True


def test_apply_security_and_limits_adds_limit_when_missing():
    sql = apply_security_and_limits("SELECT id FROM items", "sqlite", limit=10)

    assert sql == "SELECT id FROM items LIMIT 10"


def test_apply_security_and_limits_preserves_existing_limit():
    sql = apply_security_and_limits("SELECT id FROM items LIMIT 3", "sqlite", limit=10)

    assert sql == "SELECT id FROM items LIMIT 3"


def test_apply_security_and_limits_injects_applicable_rls_policy():
    sql = apply_security_and_limits(
        "SELECT id FROM items",
        "sqlite",
        limit=10,
        rls_policies=[RLSPolicy(column="tenant_id", value="tenant-1")],
        schema=schema_with_tenant_column(),
    )

    assert "FROM (SELECT * FROM items WHERE tenant_id = 'tenant-1') AS items" in sql
    assert sql.endswith("LIMIT 10")


def test_apply_security_and_limits_skips_rls_policy_when_column_is_absent():
    sql = apply_security_and_limits(
        "SELECT id FROM items",
        "sqlite",
        limit=10,
        rls_policies=[RLSPolicy(column="missing_tenant_id", value="tenant-1")],
        schema=schema_with_tenant_column(),
    )

    assert "missing_tenant_id" not in sql
    assert sql == "SELECT id FROM items LIMIT 10"


def test_clean_generated_sql_strips_markdown_fences_and_newlines():
    assert clean_generated_sql("```sql\nSELECT *\nFROM users\n```") == "SELECT * FROM users"
    assert clean_generated_sql("```\nSELECT 1\n```") == "SELECT 1"
    assert clean_generated_sql("  SELECT 2  ") == "SELECT 2"


def test_summarize_result_handles_dataframes_none_and_unrecognized_values():
    df = pl.DataFrame({"id": [1, 2], "name": ["a", "b"]})

    assert summarize_result(df) == "Rows: 2; Columns: id, name"
    assert summarize_result(None) is None
    assert summarize_result(object()) is None


def test_timeout_statement_helpers_return_expected_dialect_specific_sql():
    assert build_timeout_statement("postgres", 1500) == "SET statement_timeout = 1500"
    assert build_timeout_statement("mysql", 1500) == "SET SESSION MAX_EXECUTION_TIME = 1500"
    assert build_timeout_statement("mssql", 1500) == "SET LOCK_TIMEOUT 1500"
    assert build_timeout_statement("sqlite", 1500) is None
    assert build_async_timeout_statement("mssql", 1500) is None
    assert build_async_timeout_statement("postgres", 1500) == "SET statement_timeout = 1500"


def test_build_generator_prompt_includes_mssql_schema_prefix_and_context_blocks():
    config = GenQueryConfig(connection_string="sqlite://", schema_name="analytics")
    schema = schema_with_tenant_column().model_copy(update={"dialect": "mssql"})
    step = PlanStep(id="step_1", description="List items")

    prompt = build_generator_prompt(
        config,
        step,
        schema,
        error_context="bad column",
        previous_results="id\n1",
        conversation_context="Turn 1 context",
    )

    assert "analytics.items" in prompt
    assert "List items" in prompt
    assert "bad column" in prompt
    assert "id\n1" in prompt
    assert "Turn 1 context" in prompt

import os
import time

import pytest

from genquery.config import GenQueryConfig, RLSPolicy, TableFilterConfig
from genquery.core.models import ColumnMetadata, SchemaContext, TableMetadata
from genquery.pipeline.inspector.cache import SchemaCache
from genquery.pipeline.inspector.filters import should_include_table


def test_config_from_yaml_requires_existing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        GenQueryConfig.from_yaml(str(tmp_path / "missing.yaml"))


def test_config_from_yaml_requires_connection_string_when_not_overridden(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text("schema_name: analytics\n", encoding="utf-8")

    with pytest.raises(ValueError, match="connection_string"):
        GenQueryConfig.from_yaml(str(config_path))


def test_config_from_yaml_applies_overrides_and_merges_connect_args(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "\n".join(
            [
                "connection_string: sqlite:///original.db",
                "schema_name: public",
                "row_limit: 25",
                "connect_args:",
                "  timeout: 5",
                "table_filters:",
                "  exclude:",
                "    - audit_log",
                "rls_policies:",
                "  - column: tenant_id",
                "    value: tenant-1",
                "    session_variable: app.tenant_id",
            ]
        ),
        encoding="utf-8",
    )

    config = GenQueryConfig.from_yaml(
        str(config_path),
        connection_string="sqlite:///override.db",
        schema_name="analytics",
        connect_args={"check_same_thread": False},
    )

    assert config.connection_string == "sqlite:///override.db"
    assert config.schema_name == "analytics"
    assert config.row_limit == 25
    assert config.connect_args == {"timeout": 5, "check_same_thread": False}
    assert config.table_filters.exclude == ["audit_log"]
    assert config.rls_policies == [
        RLSPolicy(column="tenant_id", value="tenant-1", session_variable="app.tenant_id")
    ]


def test_table_filters_support_include_exclude_prefix_suffix_and_regex():
    assert should_include_table("orders", TableFilterConfig(include=["orders"])) is True
    assert should_include_table("customers", TableFilterConfig(include=["orders"])) is False
    assert should_include_table("audit_log", TableFilterConfig(exclude=["audit_log"])) is False
    assert should_include_table("app_orders", TableFilterConfig(prefix="app_")) is True
    assert should_include_table("orders", TableFilterConfig(prefix="app_")) is False
    assert should_include_table("orders_view", TableFilterConfig(suffix="_view")) is True
    assert should_include_table("orders", TableFilterConfig(suffix="_view")) is False
    assert should_include_table("fact_sales", TableFilterConfig(regex=r"^fact_")) is True
    assert should_include_table("dim_customer", TableFilterConfig(regex=r"^fact_")) is False


def make_schema() -> SchemaContext:
    return SchemaContext(
        dialect="sqlite",
        tables=[
            TableMetadata(
                name="users",
                columns=[
                    ColumnMetadata(name="id", type="INTEGER", primary_key=True, nullable=False),
                    ColumnMetadata(name="name", type="TEXT", primary_key=False, nullable=True),
                ],
            )
        ],
    )


def test_schema_cache_round_trips_schema_context(tmp_path):
    config = GenQueryConfig(
        connection_string="sqlite:///cache-test.db",
        schema_cache_dir=str(tmp_path),
        schema_cache_ttl_seconds=60,
    )
    cache = SchemaCache(config)
    schema = make_schema()

    assert cache.get() is None
    cache.set(schema)

    cached = cache.get()
    assert cached == schema
    assert cache.should_refresh_soon(threshold=0.8) is False


def test_schema_cache_respects_disabled_ttl(tmp_path):
    config = GenQueryConfig(
        connection_string="sqlite:///cache-disabled.db",
        schema_cache_dir=str(tmp_path),
        schema_cache_ttl_seconds=0,
    )
    cache = SchemaCache(config)

    cache.set(make_schema())

    assert cache.get() is None
    assert os.listdir(tmp_path) == []
    assert cache.should_refresh_soon() is False


def test_schema_cache_treats_expired_files_as_misses(tmp_path):
    config = GenQueryConfig(
        connection_string="sqlite:///cache-expired.db",
        schema_cache_dir=str(tmp_path),
        schema_cache_ttl_seconds=1,
    )
    cache = SchemaCache(config)
    cache.set(make_schema())
    cache_path = cache._get_cache_path()
    old_time = time.time() - 10
    os.utime(cache_path, (old_time, old_time))

    assert cache.get() is None
    assert cache.should_refresh_soon(threshold=0.8) is True

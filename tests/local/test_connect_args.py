import pytest
import os
import yaml
from unittest.mock import MagicMock
from genquery.config import GenQueryConfig
from genquery.genquery import GenQuery
from genquery.adapters.base import LLMAdapter

class MockLLMAdapter(LLMAdapter):
    def generate(self, prompt: str) -> str:
        return "SELECT 1"

def test_config_connect_args():
    config = GenQueryConfig(
        connection_string="sqlite:///:memory:",
        connect_args={"timeout": 30, "check_same_thread": False}
    )
    assert config.connect_args["timeout"] == 30
    assert config.connect_args["check_same_thread"] is False

def test_genquery_init_connect_args_override():
    llm = MockLLMAdapter()
    gq = GenQuery(
        llm=llm,
        connection_string="sqlite:///:memory:",
        connect_args={"timeout": 60}
    )
    # The dictionary passed to sqlalchemy engine
    # In sqlite, create_engine does not introspect connect_args to engine.url but we can check the config
    assert gq.config.connect_args["timeout"] == 60

def test_genquery_init_connect_args_merge_with_config():
    llm = MockLLMAdapter()
    base_config = GenQueryConfig(
        connection_string="sqlite:///:memory:",
        connect_args={"timeout": 30, "check_same_thread": False}
    )
    gq = GenQuery(
        llm=llm,
        config=base_config,
        connect_args={"timeout": 60, "isolation_level": "AUTOCOMMIT"}
    )

    assert gq.config.connect_args["timeout"] == 60
    assert gq.config.connect_args["check_same_thread"] is False
    assert gq.config.connect_args["isolation_level"] == "AUTOCOMMIT"

def test_genquery_init_connect_args_postgres_schema(tmp_path):
    llm = MockLLMAdapter()
    gq = GenQuery(
        llm=llm,
        connection_string="postgresql://user:pass@localhost/db",
        schema="my_schema",
        connect_args={"keepalives": 1}
    )

    # Engine is created with a modified dictionary. We can't easily inspect engine connect_args
    # but we can verify it doesn't crash and the schema logic handled options correctly in our config or args if we mocked
    # Actually, SQLAlchemy's Engine does expose some details, but let's just ensure it initializes without error
    assert gq.config.connect_args["keepalives"] == 1
    assert "postgre" in gq.engine.url.drivername

def test_genquery_config_yaml_merge(tmp_path):
    yaml_file = tmp_path / "config.yaml"
    with open(yaml_file, "w") as f:
        yaml.dump({
            "connection_string": "sqlite:///:memory:",
            "connect_args": {"timeout": 15, "mode": "ro"}
        }, f)

    config = GenQueryConfig.from_yaml(
        str(yaml_file),
        connect_args={"timeout": 45, "cache": "shared"}
    )

    assert config.connect_args["timeout"] == 45
    assert config.connect_args["mode"] == "ro"
    assert config.connect_args["cache"] == "shared"

import sqlite3
import pytest
import tempfile
import os
from sqlalchemy import create_engine
from genquery.config import GenQueryConfig, TableFilterConfig
from genquery.pipeline.inspector.inspector import SchemaInspectorStage

def setup_test_db(db_path: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT);")
    cursor.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, user_id INTEGER, amount REAL, FOREIGN KEY(user_id) REFERENCES users(id));")
    cursor.execute("CREATE TABLE _audit_log (id INTEGER PRIMARY KEY, event TEXT);")
    conn.commit()
    conn.close()

def test_inspector():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
        
    engine = None
    try:
        setup_test_db(path)
        
        config = GenQueryConfig(
            connection_string=f"sqlite:///{path}",
            table_filters=TableFilterConfig(exclude=["_audit_log"])
        )
        
        engine = create_engine(config.connection_string, connect_args=config.connect_args)
        inspector = SchemaInspectorStage(engine, config)
        schema = inspector.get_schema()
        
        assert schema.dialect == "sqlite"
        assert len(schema.tables) == 2
        table_names = [t.name for t in schema.tables]
        assert "users" in table_names
        assert "orders" in table_names
        assert "_audit_log" not in table_names
        
        users_meta = next(t for t in schema.tables if t.name == "users")
        assert len(users_meta.columns) == 3
        
        id_col = next(c for c in users_meta.columns if c.name == "id")
        assert id_col.primary_key is True
    finally:
        if engine is not None:
            engine.dispose()
        os.remove(path)

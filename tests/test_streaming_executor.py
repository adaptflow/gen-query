import asyncio
import os
import sqlite3
import tempfile

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine

from genquery.config import GenQueryConfig
from genquery.core.models import ColumnMetadata, PlanStep, QueryPlan, SchemaContext, TableMetadata
from genquery.pipeline.executor.executor import AsyncQueryExecutorStage, QueryExecutorStage
from genquery.pipeline.executor.validator import SecurityValidator


class StaticLLM:
    def __init__(self, sql: str):
        self.sql = sql

    def complete(self, messages, **kwargs):
        return self.sql


class AsyncStaticLLM:
    def __init__(self, sql: str):
        self.sql = sql

    async def acomplete(self, messages, **kwargs):
        return self.sql


def create_sqlite_db(path: str) -> None:
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT)")
    cursor.executemany(
        "INSERT INTO items (id, name) VALUES (?, ?)",
        [(index, f"item-{index}") for index in range(1, 8)],
    )
    conn.commit()
    conn.close()


def item_schema() -> SchemaContext:
    return SchemaContext(
        dialect="sqlite",
        tables=[
            TableMetadata(
                name="items",
                columns=[
                    ColumnMetadata(name="id", type="INTEGER", primary_key=True, nullable=False),
                    ColumnMetadata(name="name", type="TEXT", primary_key=False, nullable=True),
                ],
            )
        ],
    )


def item_plan() -> QueryPlan:
    return QueryPlan(
        strategy="single",
        steps=[PlanStep(id="step_1", description="List items")],
    )


def test_sync_executor_streams_final_result_as_polars_batches_and_respects_row_limit():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as db_file:
        db_path = db_file.name

    engine = None
    try:
        create_sqlite_db(db_path)
        config = GenQueryConfig(
            connection_string=f"sqlite:///{db_path}",
            row_limit=5,
            stream_batch_size=2,
        )
        engine = create_engine(config.connection_string)
        executor = QueryExecutorStage(
            StaticLLM("SELECT id, name FROM items ORDER BY id"),
            engine,
            SecurityValidator("sqlite"),
            config,
        )

        stream = executor.execute_plan(
            item_plan(),
            item_schema(),
            stream_results=True,
            batch_size=2,
        )

        with stream:
            batches = list(stream)

        assert [batch.shape for batch in batches] == [(2, 2), (2, 2), (1, 2)]
        assert sum(len(batch) for batch in batches) == 5
        assert batches[0]["id"].to_list() == [1, 2]
    finally:
        if engine is not None:
            engine.dispose()
        os.remove(db_path)


def test_sync_executor_stream_yields_one_empty_batch_for_empty_results():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as db_file:
        db_path = db_file.name

    engine = None
    try:
        create_sqlite_db(db_path)
        config = GenQueryConfig(connection_string=f"sqlite:///{db_path}", stream_batch_size=2)
        engine = create_engine(config.connection_string)
        executor = QueryExecutorStage(
            StaticLLM("SELECT id, name FROM items WHERE id < 0"),
            engine,
            SecurityValidator("sqlite"),
            config,
        )

        stream = executor.execute_plan(item_plan(), item_schema(), stream_results=True, batch_size=2)

        with stream:
            batches = list(stream)

        assert len(batches) == 1
        assert batches[0].shape == (0, 2)
        assert batches[0].columns == ["id", "name"]
    finally:
        if engine is not None:
            engine.dispose()
        os.remove(db_path)


def test_async_executor_streams_final_result_as_polars_batches_and_respects_row_limit():
    async def run_test():
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as db_file:
            db_path = db_file.name

        engine = None
        try:
            create_sqlite_db(db_path)
            config = GenQueryConfig(
                connection_string=f"sqlite+aiosqlite:///{db_path}",
                row_limit=5,
                stream_batch_size=2,
            )
            engine = create_async_engine(config.connection_string)
            executor = AsyncQueryExecutorStage(
                AsyncStaticLLM("SELECT id, name FROM items ORDER BY id"),
                engine,
                SecurityValidator("sqlite"),
                config,
            )

            stream = await executor.execute_plan(
                item_plan(),
                item_schema(),
                stream_results=True,
                batch_size=2,
            )

            batches = []
            async with stream:
                async for batch in stream:
                    batches.append(batch)

            assert [batch.shape for batch in batches] == [(2, 2), (2, 2), (1, 2)]
            assert sum(len(batch) for batch in batches) == 5
            assert batches[0]["id"].to_list() == [1, 2]
        finally:
            if engine is not None:
                await engine.dispose()
            os.remove(db_path)

    asyncio.run(run_test())

from typing import Any, Dict, List, Optional
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from genquery.adapters.base import AsyncLLMAdapter
from genquery.config import GenQueryConfig, TableFilterConfig
from genquery.pipeline.pipeline import AsyncGenQueryPipeline, QueryResult
from genquery.pipeline.state import AsyncPipelineStage, PipelineState
from genquery.pipeline.inspector.inspector import AsyncSchemaInspectorStage
from genquery.pipeline.ranker.ranker import AsyncSemanticRankerStage
from genquery.pipeline.planner.planner import AsyncQueryPlannerStage
from genquery.pipeline.executor.executor import AsyncQueryExecutorStage
from genquery.pipeline.executor.validator import SecurityValidator
from genquery.core.callbacks import AsyncGenQueryCallbackHandler, ensure_async_callback_handler
from genquery.core.models import ConversationTurn
from genquery.core.utils import get_dialect

class AsyncGenQuery:
    """
    Async orchestrator class for the GenQuery system.

    Provides an asyncio-compatible facade for initializing and executing the
    pipeline in highly concurrent web applications. Use async SQLAlchemy URLs
    such as postgresql+asyncpg://, sqlite+aiosqlite://, mysql+asyncmy://,
    mssql+aioodbc://, or oracle+oracledb:// where supported by SQLAlchemy and
    the installed DBAPI driver.
    """
    def __init__(
        self,
        llm: AsyncLLMAdapter,
        connection_string: Optional[str] = None,
        schema: str = "public",
        config: Optional[GenQueryConfig] = None,
        connect_args: Optional[Dict[str, Any]] = None,
        table_filter: Optional[Dict[str, Any]] = None,
        config_path: Optional[str] = None,
        callbacks: Optional[AsyncGenQueryCallbackHandler] = None,
        custom_stages: Optional[List[AsyncPipelineStage]] = None,
        engine: Optional[AsyncEngine] = None,
    ):
        if config is not None:
            self.config = config
            if connect_args:
                self.config.connect_args = {**self.config.connect_args, **connect_args}
        elif config_path:
            self.config = GenQueryConfig.from_yaml(
                config_path,
                connection_string=connection_string,
                schema_name=schema,
                connect_args=connect_args
            )
        else:
            filter_config = TableFilterConfig(**table_filter) if table_filter else TableFilterConfig()
            self.config = GenQueryConfig(
                connection_string=connection_string,
                schema_name=schema,
                connect_args=connect_args or {},
                table_filters=filter_config
            )

        self.llm = llm
        self.callbacks = ensure_async_callback_handler(callbacks)

        if engine is not None:
            self.engine = engine
        else:
            engine_connect_args = self.config.connect_args.copy()

            if self.config.connection_string and self.config.connection_string.startswith("postgre"):
                if "+asyncpg" in self.config.connection_string:
                    server_settings = engine_connect_args.setdefault("server_settings", {})
                    server_settings.setdefault("search_path", self.config.schema_name)
                elif 'options' not in engine_connect_args:
                    engine_connect_args['options'] = f'-csearch_path={self.config.schema_name}'
                elif '-csearch_path' not in engine_connect_args['options']:
                    engine_connect_args['options'] += f' -csearch_path={self.config.schema_name}'

            self.engine = create_async_engine(self.config.connection_string, connect_args=engine_connect_args)

        dialect_name = get_dialect(self.engine)

        if dialect_name == "oracle" and self.config.schema_name:
            @event.listens_for(self.engine.sync_engine, "connect", insert=True)
            def set_oracle_schema(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute(f'ALTER SESSION SET CURRENT_SCHEMA = "{self.config.schema_name}"')
                cursor.close()

        self.validator = SecurityValidator(dialect=dialect_name)

        if custom_stages is not None:
            self.pipeline = AsyncGenQueryPipeline(stages=custom_stages)
        else:
            self.pipeline = self._build_default_pipeline()

    def _build_default_pipeline(self) -> AsyncGenQueryPipeline:
        pipeline = AsyncGenQueryPipeline()
        pipeline.add_stage(AsyncSchemaInspectorStage(self.engine, self.config, self.callbacks))
        pipeline.add_stage(AsyncSemanticRankerStage(self.llm, self.config, self.callbacks))
        pipeline.add_stage(AsyncQueryPlannerStage(self.llm, self.config, self.callbacks))
        pipeline.add_stage(AsyncQueryExecutorStage(self.llm, self.engine, self.validator, self.config, self.callbacks))
        return pipeline

    async def generate(
        self,
        query: str,
        conversation: Optional[List[ConversationTurn]] = None,
    ) -> QueryResult:
        """
        Generate SQL, plan, and execute the query, matching the sync API behavior.
        """
        state = PipelineState(
            query=query,
            conversation=conversation or [],
            context={"dry_run": False}
        )
        return await self.pipeline.execute(state)

    async def stream(
        self,
        query: str,
        conversation: Optional[List[ConversationTurn]] = None,
        batch_size: Optional[int] = None,
    ) -> QueryResult:
        """
        Generate SQL, plan, and return a QueryResult with an async final-result stream.

        The stream yields Polars DataFrame batches, respects the configured
        row_limit, and should be consumed fully or closed explicitly. Use it as
        an async context manager when you may exit iteration early:

            result = await gq.stream("show orders")
            async with result.stream as batches:
                async for batch in batches:
                    ...
        """
        state = PipelineState(
            query=query,
            conversation=conversation or [],
            context={
                "dry_run": False,
                "stream_results": True,
                "stream_batch_size": batch_size or self.config.stream_batch_size,
            }
        )
        return await self.pipeline.execute(state)

    async def run(
        self,
        query: str,
        conversation: Optional[List[ConversationTurn]] = None,
        return_result: bool = False,
    ) -> Any:
        """
        Generate SQL, plan, and execute the query asynchronously.

        By default this returns the resulting DataFrame. Set return_result=True
        to receive a QueryResult containing SQL, plan, DataFrame, and updated
        conversation history for multi-turn follow-ups.
        """
        state = PipelineState(
            query=query,
            conversation=conversation or [],
            context={"dry_run": False}
        )
        result = await self.pipeline.execute(state)
        if return_result:
            return result
        return result.df

    async def close(self) -> None:
        """Dispose the async SQLAlchemy engine and close pooled connections."""
        await self.engine.dispose()

    async def __aenter__(self) -> "AsyncGenQuery":
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        await self.close()

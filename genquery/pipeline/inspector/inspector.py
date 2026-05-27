from genquery.core.utils import get_dialect
from sqlalchemy import Engine
from sqlalchemy.ext.asyncio import AsyncEngine

from sqlalchemy import inspect
from typing import Any, List, Optional

from genquery.pipeline.inspector.filters import should_include_table
from genquery.core.models import SchemaContext, TableMetadata, ColumnMetadata, IndexMetadata
from genquery.config import GenQueryConfig
from genquery.core.callbacks import AsyncGenQueryCallbackHandler, GenQueryCallbackHandler, ensure_async_callback_handler

from genquery.pipeline.state import AsyncPipelineStage, PipelineStage, PipelineState

from genquery.pipeline.inspector.cache import SchemaCache
from genquery.logging import get_logger
import asyncio
import threading


logger = get_logger(__name__)


def inspect_schema(bind: Any, config: GenQueryConfig) -> SchemaContext:
    """Inspect a sync SQLAlchemy bind and return a reusable schema context."""
    inspector = inspect(bind)
    dialect_name = get_dialect(bind)

    schema_kwargs = {}
    if dialect_name != "sqlite" and config.schema_name:
        schema_kwargs["schema"] = config.schema_name

    tables: List[TableMetadata] = []
    try:
        table_names = inspector.get_table_names(**schema_kwargs)
    except Exception as exc:
        logger.warning(
            "Schema-specific table inspection failed for schema=%s; falling back to default schema: %s",
            config.schema_name,
            exc,
        )
        # Fallback if specific schema fails or is unsupported.
        table_names = inspector.get_table_names()

    filtered_tables = [t for t in table_names if should_include_table(t, config.table_filters)]

    use_multi = False
    use_multi_comments = False
    multi_columns = {}
    multi_pk = {}
    multi_indexes = {}
    multi_comments = {}
    multi_fks = {}

    if hasattr(inspector, "get_multi_columns") and filtered_tables:
        try:
            schema_val = schema_kwargs.get("schema")
            multi_columns = inspector.get_multi_columns(schema=schema_val, filter_names=filtered_tables)
            multi_pk = inspector.get_multi_pk_constraint(schema=schema_val, filter_names=filtered_tables)
            multi_indexes = inspector.get_multi_indexes(schema=schema_val, filter_names=filtered_tables)
            multi_fks = inspector.get_multi_foreign_keys(schema=schema_val, filter_names=filtered_tables)
            use_multi = True

            try:
                multi_comments = inspector.get_multi_table_comment(schema=schema_val, filter_names=filtered_tables)
                use_multi_comments = True
            except NotImplementedError:
                logger.debug("Bulk table comments are not supported by this dialect")
        except Exception as exc:
            logger.debug("Bulk schema inspection unavailable; falling back to per-table inspection: %s", exc)

    for table_name in filtered_tables:
        columns_meta = []
        schema_tb = (schema_kwargs.get("schema"), table_name)

        if use_multi:
            pk_constraint = multi_pk.get(schema_tb, {})
            cols = multi_columns.get(schema_tb, [])
            idxs = multi_indexes.get(schema_tb, [])
            fks = multi_fks.get(schema_tb, [])
        else:
            pk_constraint = inspector.get_pk_constraint(table_name, **schema_kwargs)
            cols = inspector.get_columns(table_name, **schema_kwargs)
            idxs = inspector.get_indexes(table_name, **schema_kwargs)
            fks = inspector.get_foreign_keys(table_name, **schema_kwargs)

        pk_columns = pk_constraint.get("constrained_columns", [])

        for col in cols:
            columns_meta.append(ColumnMetadata(
                name=col["name"],
                type=str(col["type"]),
                primary_key=col["name"] in pk_columns,
                nullable=col.get("nullable", True)
            ))

        indexes_meta = []
        for idx in idxs:
            indexes_meta.append(IndexMetadata(
                name=idx.get("name", ""),
                column_names=idx.get("column_names", []),
                unique=idx.get("unique", False)
            ))

        if use_multi_comments:
            comment = multi_comments.get(schema_tb, {})
            description = comment.get("text")
        else:
            try:
                comment = inspector.get_table_comment(table_name, **schema_kwargs)
                description = comment.get("text")
            except Exception:
                description = None

        tables.append(TableMetadata(
            name=table_name,
            description=description,
            columns=columns_meta,
            foreign_keys=fks,
            indexes=indexes_meta
        ))

    return SchemaContext(tables=tables, dialect=dialect_name)


class SchemaInspectorStage(PipelineStage):
    """
    Stage 1: Extract and cache the database schema.
    """
    def __init__(self, engine: Engine, config: GenQueryConfig, callbacks: Optional[GenQueryCallbackHandler] = None):
        self.config = config
        self.engine = engine
        self.callbacks = callbacks or GenQueryCallbackHandler()
        self.cache = SchemaCache(config)

    def run(self, state: PipelineState) -> PipelineState:
        if state.schema_context is not None:
            logger.debug("Skipping schema inspection because schema context is already populated")
            # Skip if schema context was already provided by developer
            return state
            
        # Try Cache First
        cached_schema = self.cache.get()
        if cached_schema:
            logger.debug("Using cached schema context with %s tables", len(cached_schema.tables))
            state.schema_context = cached_schema
            # If approaching TTL, refresh in background
            if self.cache.should_refresh_soon():
                self._trigger_background_refresh()
            return state

        # If empty or expired, block and fetch
        state.schema_context = self.get_schema()
        self.cache.set(state.schema_context)
        
        return state
        
    def _trigger_background_refresh(self):
        def refresh_job():
            try:
                new_schema = self.get_schema()
                self.cache.set(new_schema)
            except Exception:
                logger.exception("Background schema cache refresh failed")
        t = threading.Thread(target=refresh_job, daemon=True)
        t.start()

    def get_schema(self) -> SchemaContext:
        self.callbacks.on_inspector_start()
        logger.debug("Inspecting database schema")
        schema_context = inspect_schema(self.engine, self.config)
        logger.debug("Schema inspection completed with %s tables", len(schema_context.tables))
        self.callbacks.on_inspector_end(len(schema_context.tables))
        return schema_context


class AsyncSchemaInspectorStage(AsyncPipelineStage):
    """
    Async Stage 1: Extract and cache the database schema using SQLAlchemy async engines.
    """
    def __init__(self, engine: AsyncEngine, config: GenQueryConfig, callbacks: Optional[AsyncGenQueryCallbackHandler] = None):
        self.config = config
        self.engine = engine
        self.callbacks = ensure_async_callback_handler(callbacks)
        self.cache = SchemaCache(config)


    async def run(self, state: PipelineState) -> PipelineState:
        if state.schema_context is not None:
            logger.debug("Skipping async schema inspection because schema context is already populated")
            return state

        cached_schema = self.cache.get()
        if cached_schema:
            logger.debug("Using cached async schema context with %s tables", len(cached_schema.tables))
            state.schema_context = cached_schema
            if self.cache.should_refresh_soon():
                self._trigger_background_refresh()
            return state

        state.schema_context = await self.get_schema()
        self.cache.set(state.schema_context)
        return state

    def _trigger_background_refresh(self):
        async def refresh_job():
            try:
                new_schema = await self.get_schema()
                self.cache.set(new_schema)
            except Exception:
                logger.exception("Async background schema cache refresh failed")
        try:
            asyncio.create_task(refresh_job())
        except RuntimeError as exc:
            logger.warning("Unable to start async schema cache refresh task: %s", exc)

    async def get_schema(self) -> SchemaContext:
        await self.callbacks.aon_inspector_start()
        logger.debug("Inspecting database schema asynchronously")

        async with self.engine.connect() as conn:
            schema_context = await conn.run_sync(lambda sync_connection: inspect_schema(sync_connection, self.config))

        logger.debug("Async schema inspection completed with %s tables", len(schema_context.tables))
        await self.callbacks.aon_inspector_end(len(schema_context.tables))
        return schema_context


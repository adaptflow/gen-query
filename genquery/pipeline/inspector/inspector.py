from genquery.core.utils import get_dialect
from sqlalchemy import Engine
from sqlalchemy import inspect
from typing import List, Optional
from genquery.pipeline.inspector.filters import should_include_table
from genquery.core.models import SchemaContext, TableMetadata, ColumnMetadata, IndexMetadata
from genquery.config import GenQueryConfig
from genquery.core.callbacks import GenQueryCallbackHandler
from genquery.pipeline.state import PipelineStage, PipelineState
from genquery.pipeline.inspector.cache import SchemaCache
import threading

class SchemaInspectorStage(PipelineStage):
    def __init__(self, engine: Engine, config: GenQueryConfig, callbacks: Optional[GenQueryCallbackHandler] = None):
        self.config = config
        self.engine = engine
        self.callbacks = callbacks or GenQueryCallbackHandler()
        self.cache = SchemaCache(config)

    def run(self, state: PipelineState) -> PipelineState:
        if state.schema_context is not None:
            # Skip if schema context was already provided by developer
            return state
            
        # Try Cache First
        cached_schema = self.cache.get()
        if cached_schema:
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
            except Exception as e:
                pass # Safe background failure
        t = threading.Thread(target=refresh_job, daemon=True)
        t.start()

    def get_schema(self) -> SchemaContext:
        self.callbacks.on_inspector_start()
        
        inspector = inspect(self.engine)
        dialect_name = get_dialect(self.engine)
        
        # Determine schema argument
        schema_kwargs = {}
        if dialect_name != "sqlite" and self.config.schema_name:
            schema_kwargs["schema"] = self.config.schema_name

        tables: List[TableMetadata] = []
        try:
            table_names = inspector.get_table_names(**schema_kwargs)
        except Exception as e:
            # Fallback if specific schema fails or is unsupported
            table_names = inspector.get_table_names()
            
        filtered_tables = [t for t in table_names if should_include_table(t, self.config.table_filters)]

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
                    pass
            except Exception:
                pass

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
                col_type = str(col["type"])
                columns_meta.append(ColumnMetadata(
                    name=col["name"],
                    type=col_type,
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
                except:
                    description = None
                
            tables.append(TableMetadata(
                name=table_name,
                description=description,
                columns=columns_meta,
                foreign_keys=fks,
                indexes=indexes_meta
            ))
            
        self.callbacks.on_inspector_end(len(tables))
        return SchemaContext(tables=tables, dialect=dialect_name)

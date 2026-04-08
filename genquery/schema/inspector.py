from sqlalchemy import create_engine, inspect
from typing import List, Optional
from .filters import should_include_table
from genquery.core.context import SchemaContext, TableMetadata, ColumnMetadata, IndexMetadata
from genquery.config import GenQueryConfig
from genquery.core.callbacks import GenQueryCallbackHandler

class SchemaInspector:
    def __init__(self, config: GenQueryConfig, callbacks: Optional[GenQueryCallbackHandler] = None):
        self.config = config
        self.engine = create_engine(config.connection_string)
        self.callbacks = callbacks or GenQueryCallbackHandler()

    def get_schema(self) -> SchemaContext:
        self.callbacks.on_inspector_start()
        
        inspector = inspect(self.engine)
        dialect_name = self.engine.dialect.name
        
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

        for table_name in filtered_tables:
            columns_meta = []
            pk_constraint = inspector.get_pk_constraint(table_name, **schema_kwargs)
            pk_columns = pk_constraint.get("constrained_columns", [])
            
            for col in inspector.get_columns(table_name, **schema_kwargs):
                col_type = str(col["type"])
                columns_meta.append(ColumnMetadata(
                    name=col["name"],
                    type=col_type,
                    primary_key=col["name"] in pk_columns,
                    nullable=col.get("nullable", True)
                ))

            indexes_meta = []
            for idx in inspector.get_indexes(table_name, **schema_kwargs):
                indexes_meta.append(IndexMetadata(
                    name=idx.get("name", ""),
                    column_names=idx.get("column_names", []),
                    unique=idx.get("unique", False)
                ))
                
            try:
                comment = inspector.get_table_comment(table_name, **schema_kwargs)
                description = comment.get("text")
            except:
                description = None
                
            tables.append(TableMetadata(
                name=table_name,
                description=description,
                columns=columns_meta,
                foreign_keys=inspector.get_foreign_keys(table_name, **schema_kwargs),
                indexes=indexes_meta
            ))
            
        self.callbacks.on_inspector_end(len(tables))
        return SchemaContext(tables=tables, dialect=dialect_name)

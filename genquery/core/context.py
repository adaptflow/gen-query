from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class ColumnMetadata(BaseModel):
    name: str
    type: str
    primary_key: bool
    nullable: bool

class IndexMetadata(BaseModel):
    name: str
    column_names: List[str]
    unique: bool

class TableMetadata(BaseModel):
    name: str
    description: Optional[str] = None
    columns: List[ColumnMetadata]
    foreign_keys: List[Dict[str, Any]] = []
    indexes: List[IndexMetadata] = []

class SchemaContext(BaseModel):
    tables: List[TableMetadata]
    dialect: str

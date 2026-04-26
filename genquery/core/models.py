from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class ColumnMetadata(BaseModel):
    """Metadata representing a database table column."""
    name: str
    type: str
    primary_key: bool
    nullable: bool

class IndexMetadata(BaseModel):
    """Metadata representing a database index."""
    name: str
    column_names: List[str]
    unique: bool

class TableMetadata(BaseModel):
    """Metadata representing a database table."""
    name: str
    description: Optional[str] = None
    columns: List[ColumnMetadata]
    foreign_keys: List[Dict[str, Any]] = []
    indexes: List[IndexMetadata] = []

class SchemaContext(BaseModel):
    """Contextual representation of the database schema."""
    tables: List[TableMetadata]
    dialect: str

class PlanStep(BaseModel):
    """A single step within a query execution plan."""
    id: str
    description: str
    depends_on: List[str] = []
    output_alias: Optional[str] = None
    receives_context: Optional[str] = None

class QueryPlan(BaseModel):
    """A complete query execution plan."""
    strategy: str  # "single", "sequential", "parallel"
    steps: List[PlanStep]

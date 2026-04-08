from pydantic import BaseModel, Field
from typing import List, Optional, Pattern, Any

class TableFilterConfig(BaseModel):
    include: Optional[List[str]] = None
    exclude: Optional[List[str]] = None
    regex: Optional[Pattern | str] = None
    prefix: Optional[str] = None
    suffix: Optional[str] = None

class GenQueryConfig(BaseModel):
    connection_string: str
    schema_name: str = "public"
    table_filters: TableFilterConfig = Field(default_factory=TableFilterConfig)

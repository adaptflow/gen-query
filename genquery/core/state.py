from pydantic import BaseModel, ConfigDict, Field
from typing import Any, Dict, Optional, List
from genquery.core.context import SchemaContext
from genquery.planner.plan_models import QueryPlan

class PipelineState(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    query: str
    schema_context: Optional[SchemaContext] = None
    ranked_schema: Optional[SchemaContext] = None
    plan: Optional[QueryPlan] = None
    sql: Optional[str] = None
    df: Optional[Any] = None
    
    # Context dictionary to pass arbitrary data between custom stages
    context: Dict[str, Any] = Field(default_factory=dict)

class PipelineStage:
    """
    Abstract base class for a pipeline stage.
    """
    def run(self, state: PipelineState) -> PipelineState:
        raise NotImplementedError("PipelineStage must implement the 'run' method.")

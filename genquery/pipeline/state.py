from pydantic import BaseModel, ConfigDict, Field
from typing import Any, Dict, Optional, List
from genquery.core.models import SchemaContext, QueryPlan, ConversationTurn

class PipelineState(BaseModel):
    """
    Holds the state of the query generation pipeline.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    query: str
    schema_context: Optional[SchemaContext] = None
    ranked_schema: Optional[SchemaContext] = None
    plan: Optional[QueryPlan] = None
    sql: Optional[str] = None
    df: Optional[Any] = None
    conversation: List[ConversationTurn] = Field(default_factory=list)
    
    # Context dictionary to pass arbitrary data between custom stages
    context: Dict[str, Any] = Field(default_factory=dict)

class PipelineStage:
    """
    Abstract base class for a synchronous pipeline stage.
    """
    def run(self, state: PipelineState) -> PipelineState:
        """
        Executes the logic of this stage and returns the updated state.
        """
        raise NotImplementedError("PipelineStage must implement the 'run' method.")

class AsyncPipelineStage:
    """
    Abstract base class for an asynchronous pipeline stage.
    """
    async def run(self, state: PipelineState) -> PipelineState:
        """
        Asynchronously executes the logic of this stage and returns the updated state.
        """
        raise NotImplementedError("AsyncPipelineStage must implement the 'run' method.")


from pydantic import BaseModel
from typing import List, Optional

class PlanStep(BaseModel):
    id: str
    description: str
    depends_on: List[str] = []
    output_alias: Optional[str] = None
    receives_context: Optional[str] = None

class QueryPlan(BaseModel):
    strategy: str  # "single", "sequential", "parallel"
    steps: List[PlanStep]

from typing import Any, List, Optional
from genquery.pipeline.state import PipelineState, PipelineStage

class QueryResult:
    def __init__(self, sql: Optional[str], plan: Any, steps: Any, df: Any = None):
        self.sql = sql
        self.plan = plan
        self.steps = steps
        self.df = df

class GenQueryPipeline:
    """
    A customizable execution pipeline for GenQuery.
    Executes a list of PipelineStages sequentially.
    """
    def __init__(self, stages: Optional[List[PipelineStage]] = None):
        self.stages = stages or []
        
    def add_stage(self, stage: PipelineStage):
        self.stages.append(stage)

    def replace_stage(self, target_class: type, new_stage: PipelineStage) -> bool:
        """
        Replaces the first stage that is an instance of `target_class` with `new_stage`.
        Returns True if successful, False if no such stage was found.
        """
        for i, stage in enumerate(self.stages):
            if isinstance(stage, target_class):
                self.stages[i] = new_stage
                return True
        return False
        
    def remove_stage(self, target_class: type) -> bool:
        """
        Removes the first stage that is an instance of `target_class`.
        Returns True if successful.
        """
        for i, stage in enumerate(self.stages):
            if isinstance(stage, target_class):
                self.stages.pop(i)
                return True
        return False

    def execute(self, state: PipelineState) -> QueryResult:
        for stage in self.stages:
            state = stage.run(state)
            
        return QueryResult(
            sql=state.sql,
            plan=state.plan,
            steps=state.plan.steps if state.plan else [],
            df=state.df
        )

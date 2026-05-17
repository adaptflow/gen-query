from typing import Any, Generic, List, Optional, TypeVar
from genquery.core.models import ConversationTurn
from genquery.pipeline.state import AsyncPipelineStage, PipelineState, PipelineStage


StageT = TypeVar("StageT")


class QueryResult:
    """Represents the final result of a GenQuery execution."""
    def __init__(
        self,
        sql: Optional[str],
        plan: Any,
        steps: Any,
        df: Any = None,
        stream: Any = None,
        conversation: Optional[List[ConversationTurn]] = None,
    ):
        self.sql = sql
        self.plan = plan
        self.steps = steps
        self.df = df
        self.stream = stream
        self.conversation = conversation or []


def build_query_result(state: PipelineState) -> QueryResult:
    """Build a public query result object from the final pipeline state."""
    return QueryResult(
        sql=state.sql,
        plan=state.plan,
        steps=state.plan.steps if state.plan else [],
        df=state.df,
        stream=state.stream,
        conversation=state.conversation
    )


class PipelineStageManager(Generic[StageT]):
    """Shared stage-list management for sync and async pipelines."""
    def __init__(self, stages: Optional[List[StageT]] = None):
        self.stages = stages or []

    def add_stage(self, stage: StageT):
        """Append a stage to the end of the pipeline."""
        self.stages.append(stage)

    def replace_stage(self, target_class: type, new_stage: StageT) -> bool:
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


class AsyncGenQueryPipeline(PipelineStageManager[AsyncPipelineStage]):
    """
    A customizable asynchronous execution pipeline for GenQuery.
    Executes a list of AsyncPipelineStages sequentially.
    """

    async def execute(self, state: PipelineState) -> QueryResult:
        """
        Executes all async stages in the pipeline sequentially.
        """
        for stage in self.stages:
            state = await stage.run(state)

        return build_query_result(state)


class GenQueryPipeline(PipelineStageManager[PipelineStage]):

    """
    A customizable execution pipeline for GenQuery.
    Executes a list of PipelineStages sequentially.
    """

    def execute(self, state: PipelineState) -> QueryResult:
        """
        Executes all stages in the pipeline sequentially.
        """
        for stage in self.stages:
            state = stage.run(state)
            
        return build_query_result(state)

from typing import Any, Generic, List, Optional, TypeVar
from genquery.core.models import ConversationTurn
from genquery.pipeline.state import AsyncPipelineStage, PipelineState, PipelineStage
from genquery.logging import get_logger


StageT = TypeVar("StageT")
logger = get_logger(__name__)


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
        logger.debug("Starting async pipeline with %s stages", len(self.stages))
        for stage in self.stages:
            stage_name = type(stage).__name__
            logger.debug("Starting async pipeline stage: %s", stage_name)
            try:
                state = await stage.run(state)
            except Exception:
                logger.exception("Async pipeline stage failed: %s", stage_name)
                raise
            logger.debug("Completed async pipeline stage: %s", stage_name)

        logger.debug("Async pipeline completed")
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
        logger.debug("Starting pipeline with %s stages", len(self.stages))
        for stage in self.stages:
            stage_name = type(stage).__name__
            logger.debug("Starting pipeline stage: %s", stage_name)
            try:
                state = stage.run(state)
            except Exception:
                logger.exception("Pipeline stage failed: %s", stage_name)
                raise
            logger.debug("Completed pipeline stage: %s", stage_name)
            
        logger.debug("Pipeline completed")
        return build_query_result(state)

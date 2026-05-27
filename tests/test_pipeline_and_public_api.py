import asyncio

import polars as pl

from genquery import AsyncGenQuery, GenQuery
from genquery.config import GenQueryConfig
from genquery.core.models import ConversationTurn, PlanStep, QueryPlan
from genquery.pipeline.pipeline import GenQueryPipeline
from genquery.pipeline.state import AsyncPipelineStage, PipelineStage, PipelineState


class StaticLLM:
    def complete(self, messages, **kwargs):
        return "SELECT 1"


class AsyncStaticLLM:
    async def acomplete(self, messages, **kwargs):
        return "SELECT 1"


class SetDataFrameStage(PipelineStage):
    def __init__(self, value: int = 1):
        self.value = value

    def run(self, state: PipelineState) -> PipelineState:
        state.plan = QueryPlan(
            strategy="single",
            steps=[PlanStep(id="custom", description="Return a custom frame")],
        )
        state.sql = f"SELECT {self.value} AS value"
        state.df = pl.DataFrame({"value": [self.value]})
        state.conversation.append(
            ConversationTurn(
                user_query=state.query,
                sql=state.sql,
                plan=state.plan.model_dump(),
                result_summary="Rows: 1; Columns: value",
            )
        )
        return state


class AsyncSetDataFrameStage(AsyncPipelineStage):
    async def run(self, state: PipelineState) -> PipelineState:
        state.plan = QueryPlan(
            strategy="single",
            steps=[PlanStep(id="async_custom", description="Return a custom async frame")],
        )
        state.sql = "SELECT 2 AS value"
        state.df = pl.DataFrame({"value": [2]})
        state.conversation.append(
            ConversationTurn(
                user_query=state.query,
                sql=state.sql,
                plan=state.plan.model_dump(),
                result_summary="Rows: 1; Columns: value",
            )
        )
        return state


class MarkStage(PipelineStage):
    def __init__(self, marker: str):
        self.marker = marker

    def run(self, state: PipelineState) -> PipelineState:
        state.context.setdefault("markers", []).append(self.marker)
        state.sql = ",".join(state.context["markers"])
        return state


def test_sync_pipeline_executes_stages_and_builds_query_result():
    pipeline = GenQueryPipeline([MarkStage("first"), MarkStage("second")])

    result = pipeline.execute(PipelineState(query="hello"))

    assert result.sql == "first,second"
    assert result.plan is None
    assert result.steps == []
    assert result.conversation == []


def test_pipeline_stage_manager_replace_remove_and_add_stage():
    first = MarkStage("first")
    second = MarkStage("second")
    replacement = MarkStage("replacement")
    pipeline = GenQueryPipeline([first, second])

    assert pipeline.replace_stage(MarkStage, replacement) is True
    assert pipeline.stages == [replacement, second]
    assert pipeline.remove_stage(MarkStage) is True
    assert pipeline.stages == [second]
    pipeline.add_stage(first)
    assert pipeline.stages == [second, first]
    assert pipeline.remove_stage(str) is False
    assert pipeline.replace_stage(str, replacement) is False


def test_genquery_run_returns_dataframe_with_custom_pipeline(tmp_path):
    config = GenQueryConfig(connection_string=f"sqlite:///{tmp_path / 'custom.db'}")
    gq = GenQuery(llm=StaticLLM(), config=config, custom_stages=[SetDataFrameStage(7)])

    df = gq.run("custom query")

    assert isinstance(df, pl.DataFrame)
    assert df["value"].to_list() == [7]
    gq.engine.dispose()


def test_genquery_generate_returns_query_result_with_custom_pipeline(tmp_path):
    config = GenQueryConfig(connection_string=f"sqlite:///{tmp_path / 'generate.db'}")
    gq = GenQuery(llm=StaticLLM(), config=config, custom_stages=[SetDataFrameStage(8)])

    result = gq.generate("custom query")

    assert result.sql == "SELECT 8 AS value"
    assert result.steps[0].id == "custom"
    assert result.df["value"].to_list() == [8]
    assert result.conversation[-1].user_query == "custom query"
    gq.engine.dispose()


def test_genquery_run_can_return_full_query_result(tmp_path):
    config = GenQueryConfig(connection_string=f"sqlite:///{tmp_path / 'run-result.db'}")
    gq = GenQuery(llm=StaticLLM(), config=config, custom_stages=[SetDataFrameStage(9)])

    result = gq.run("custom query", return_result=True)

    assert result.sql == "SELECT 9 AS value"
    assert result.df["value"].to_list() == [9]
    gq.engine.dispose()


def test_genquery_repr_includes_dialect_schema_stage_count_and_llm(tmp_path):
    config = GenQueryConfig(connection_string=f"sqlite:///{tmp_path / 'repr.db'}", schema_name="main")
    gq = GenQuery(llm=StaticLLM(), config=config, custom_stages=[SetDataFrameStage()])

    representation = repr(gq)

    assert "GenQuery(" in representation
    assert "dialect=sqlite" in representation
    assert "schema=main" in representation
    assert "pipeline_stages=1" in representation
    assert "llm=StaticLLM" in representation
    gq.engine.dispose()


def test_async_genquery_run_and_context_manager_with_custom_pipeline(tmp_path):
    async def run_test():
        config = GenQueryConfig(connection_string=f"sqlite+aiosqlite:///{tmp_path / 'async.db'}")
        async with AsyncGenQuery(
            llm=AsyncStaticLLM(),
            config=config,
            custom_stages=[AsyncSetDataFrameStage()],
        ) as gq:
            df = await gq.run("async custom")
            result = await gq.run("async custom", return_result=True)
            representation = repr(gq)

        assert df["value"].to_list() == [2]
        assert result.sql == "SELECT 2 AS value"
        assert result.conversation[-1].user_query == "async custom"
        assert "AsyncGenQuery(" in representation
        assert "dialect=sqlite" in representation
        assert "pipeline_stages=1" in representation

    asyncio.run(run_test())

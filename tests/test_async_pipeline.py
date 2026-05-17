import asyncio

from genquery.core.callbacks import AsyncGenQueryCallbackHandler, GenQueryCallbackHandler, ensure_async_callback_handler
from genquery.pipeline.pipeline import AsyncGenQueryPipeline
from genquery.pipeline.state import AsyncPipelineStage, PipelineState


class AppendStage(AsyncPipelineStage):
    def __init__(self, value: str):
        self.value = value

    async def run(self, state: PipelineState) -> PipelineState:
        state.context.setdefault("order", []).append(self.value)
        state.sql = ",".join(state.context["order"])
        return state


class SyncRecordingCallbacks(GenQueryCallbackHandler):
    def __init__(self):
        self.events = []

    def on_ranker_start(self, query: str) -> None:
        self.events.append(("sync_only_ranker_start", query))


class RecordingCallbacks(AsyncGenQueryCallbackHandler):
    def __init__(self):
        self.events = []

    def on_ranker_start(self, query: str) -> None:
        self.events.append(("sync_ranker_start", query))

    async def aon_planner_start(self, query: str) -> None:
        self.events.append(("async_planner_start", query))


def test_async_pipeline_executes_stages_in_order():
    async def run_pipeline():
        pipeline = AsyncGenQueryPipeline([AppendStage("first"), AppendStage("second")])
        return await pipeline.execute(PipelineState(query="hello"))

    result = asyncio.run(run_pipeline())

    assert result.sql == "first,second"


def test_async_callbacks_are_additive_to_sync_callbacks():
    async def run_callbacks():
        callbacks = RecordingCallbacks()
        await callbacks.aon_ranker_start("query")
        await callbacks.aon_planner_start("query")
        return callbacks.events

    events = asyncio.run(run_callbacks())

    assert events == [
        ("sync_ranker_start", "query"),
        ("async_planner_start", "query"),
    ]


def test_sync_callbacks_can_be_wrapped_for_async_pipeline():
    async def run_callbacks():
        sync_callbacks = SyncRecordingCallbacks()
        async_callbacks = ensure_async_callback_handler(sync_callbacks)
        await async_callbacks.aon_ranker_start("query")
        return sync_callbacks.events

    events = asyncio.run(run_callbacks())

    assert events == [("sync_only_ranker_start", "query")]

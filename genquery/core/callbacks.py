from typing import Any

class GenQueryCallbackHandler:
    """
    Base callback handler for GenQuery pipeline events.
    """
    def on_inspector_start(self) -> None:
        """Called when the schema inspector stage begins."""
        pass
    
    def on_inspector_end(self, tables_found: int) -> None:
        """Called when the schema inspector stage ends."""
        pass

    def on_adapter_call(self, prompt: str) -> None:
        """Called before the LLM adapter is invoked."""
        pass

    def on_adapter_response(self, response: str) -> None:
        """Called after the LLM adapter returns a response."""
        pass

    def on_ranker_start(self, query: str) -> None:
        """Called when the semantic ranker stage begins."""
        pass

    def on_ranker_end(self, num_tables: int) -> None:
        """Called when the semantic ranker stage ends."""
        pass

    def on_planner_start(self, query: str) -> None:
        """Called when the query planner stage begins."""
        pass

    def on_planner_end(self, plan: Any) -> None:
        """Called when the query planner stage ends."""
        pass

    def on_sql_generated(self, step_id: str, sql: str) -> None:
        """Called when SQL is successfully generated for a step."""
        pass

    def on_retry(self, step_id: str, error: str, attempt: int) -> None:
        """Called when a query execution is retried."""
        pass

    def on_execution_success(self, step_id: str, row_count: int) -> None:
        """Called when a query execution is successful."""
        pass

class AsyncGenQueryCallbackHandler(GenQueryCallbackHandler):
    """
    Additive async callback handler for GenQuery pipeline events.

    Default async methods delegate to the synchronous callback methods so existing
    callback handlers can be reused in async pipelines. Subclasses may override
    any `aon_*` method to perform non-blocking async work.
    """
    async def aon_inspector_start(self) -> None:
        self.on_inspector_start()

    async def aon_inspector_end(self, tables_found: int) -> None:
        self.on_inspector_end(tables_found)

    async def aon_adapter_call(self, prompt: str) -> None:
        self.on_adapter_call(prompt)

    async def aon_adapter_response(self, response: str) -> None:
        self.on_adapter_response(response)

    async def aon_ranker_start(self, query: str) -> None:
        self.on_ranker_start(query)

    async def aon_ranker_end(self, num_tables: int) -> None:
        self.on_ranker_end(num_tables)

    async def aon_planner_start(self, query: str) -> None:
        self.on_planner_start(query)

    async def aon_planner_end(self, plan: Any) -> None:
        self.on_planner_end(plan)

    async def aon_sql_generated(self, step_id: str, sql: str) -> None:
        self.on_sql_generated(step_id, sql)

    async def aon_retry(self, step_id: str, error: str, attempt: int) -> None:
        self.on_retry(step_id, error, attempt)

    async def aon_execution_success(self, step_id: str, row_count: int) -> None:
        self.on_execution_success(step_id, row_count)

class AsyncCallbackAdapter(AsyncGenQueryCallbackHandler):
    """
    Wraps an existing synchronous callback handler for use by async pipelines.
    """
    def __init__(self, sync_handler: GenQueryCallbackHandler):
        self.sync_handler = sync_handler

    async def aon_inspector_start(self) -> None:
        self.sync_handler.on_inspector_start()

    async def aon_inspector_end(self, tables_found: int) -> None:
        self.sync_handler.on_inspector_end(tables_found)

    async def aon_adapter_call(self, prompt: str) -> None:
        self.sync_handler.on_adapter_call(prompt)

    async def aon_adapter_response(self, response: str) -> None:
        self.sync_handler.on_adapter_response(response)

    async def aon_ranker_start(self, query: str) -> None:
        self.sync_handler.on_ranker_start(query)

    async def aon_ranker_end(self, num_tables: int) -> None:
        self.sync_handler.on_ranker_end(num_tables)

    async def aon_planner_start(self, query: str) -> None:
        self.sync_handler.on_planner_start(query)

    async def aon_planner_end(self, plan: Any) -> None:
        self.sync_handler.on_planner_end(plan)

    async def aon_sql_generated(self, step_id: str, sql: str) -> None:
        self.sync_handler.on_sql_generated(step_id, sql)

    async def aon_retry(self, step_id: str, error: str, attempt: int) -> None:
        self.sync_handler.on_retry(step_id, error, attempt)

    async def aon_execution_success(self, step_id: str, row_count: int) -> None:
        self.sync_handler.on_execution_success(step_id, row_count)

def ensure_async_callback_handler(callbacks: Any = None) -> AsyncGenQueryCallbackHandler:
    """Return an async callback handler, wrapping sync handlers when needed."""
    if callbacks is None:
        return AsyncGenQueryCallbackHandler()
    if hasattr(callbacks, "aon_inspector_start"):
        return callbacks
    return AsyncCallbackAdapter(callbacks)

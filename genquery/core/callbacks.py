from typing import Any, Optional

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

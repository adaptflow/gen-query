from typing import Any, Optional

class GenQueryCallbackHandler:
    def on_inspector_start(self) -> None:
        pass
    
    def on_inspector_end(self, tables_found: int) -> None:
        pass

    def on_adapter_call(self, prompt: str) -> None:
        pass

    def on_adapter_response(self, response: str) -> None:
        pass

    def on_ranker_start(self, query: str) -> None:
        pass

    def on_ranker_end(self, num_tables: int) -> None:
        pass

    def on_planner_start(self, query: str) -> None:
        pass

    def on_planner_end(self, plan: Any) -> None:
        pass

    def on_sql_generated(self, step_id: str, sql: str) -> None:
        pass

    def on_retry(self, step_id: str, error: str, attempt: int) -> None:
        pass

    def on_execution_success(self, step_id: str, row_count: int) -> None:
        pass

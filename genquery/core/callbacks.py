from typing import Any

class GenQueryCallbackHandler:
    def on_inspector_start(self) -> None:
        pass
    
    def on_inspector_end(self, tables_found: int) -> None:
        pass

    def on_adapter_call(self, prompt: str) -> None:
        pass

    def on_adapter_response(self, response: str) -> None:
        pass

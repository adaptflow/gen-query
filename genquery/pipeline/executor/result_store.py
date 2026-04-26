from typing import Dict, Any

class ResultStore:
    """
    Holds intermediate results between execution steps.
    """
    def __init__(self):
        self.store: Dict[str, Any] = {}

    def save(self, key: str, data: Any) -> None:
        self.store[key] = data

    def get(self, key: str) -> Any:
        return self.store.get(key)
    
    def get_context(self, keys: list[str]) -> str:
        """
        Retrieves top n rows of stored results for context.
        """
        context = ""
        for key in keys:
            df = self.get(key)
            if df is not None:
                context += f"\nResult of {key}:\n{df.head(5).to_csv(index=False)}\n"
        return context

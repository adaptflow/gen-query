from typing import Any, Optional, Dict
from genquery.adapters.base import LLMAdapter
from genquery.config import GenQueryConfig, TableFilterConfig
from genquery.core.pipeline import GenQueryPipeline, QueryResult

class GenQuery:
    def __init__(
        self, 
        llm: LLMAdapter, 
        connection_string: str, 
        schema: str = "public", 
        table_filter: Optional[Dict[str, Any]] = None
    ):
        filter_config = TableFilterConfig(**table_filter) if table_filter else TableFilterConfig()
        config = GenQueryConfig(
            connection_string=connection_string,
            schema_name=schema,
            table_filters=filter_config
        )
        self.pipeline = GenQueryPipeline(config, llm)

    def generate(self, query: str) -> QueryResult:
        """
        Generate the SQL and Plan without executing the final query on actual data.
        It uses dry_run to ensure validation using EXPLAIN.
        """
        return self.pipeline.execute(query, dry_run=True)

    def run(self, query: str) -> Any:
        """
        Generate SQL, plan, and execute returning the resulting DataFrame.
        """
        result = self.pipeline.execute(query, dry_run=False)
        return result.df

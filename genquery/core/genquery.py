from typing import Any, Optional, Dict, List
from sqlalchemy import create_engine
from genquery.adapters.base import LLMAdapter
from genquery.config import GenQueryConfig, TableFilterConfig
from genquery.core.pipeline import GenQueryPipeline, QueryResult
from genquery.core.state import PipelineState, PipelineStage
from genquery.schema.inspector import SchemaInspectorStage
from genquery.schema.ranker import SemanticRankerStage
from genquery.planner.planner import QueryPlannerStage
from genquery.executor.executor import QueryExecutorStage
from genquery.executor.validator import SecurityValidator
from genquery.core.callbacks import GenQueryCallbackHandler
from genquery.core.utils import get_dialect

class GenQuery:
    def __init__(
        self, 
        llm: LLMAdapter, 
        connection_string: Optional[str] = None, 
        schema: str = "public", 
        table_filter: Optional[Dict[str, Any]] = None,
        config_path: Optional[str] = None,
        callbacks: Optional[GenQueryCallbackHandler] = None,
        custom_stages: Optional[List[PipelineStage]] = None
    ):
        if config_path:
            self.config = GenQueryConfig.from_yaml(config_path, connection_string=connection_string, schema_name=schema)
        else:
            filter_config = TableFilterConfig(**table_filter) if table_filter else TableFilterConfig()
            self.config = GenQueryConfig(
                connection_string=connection_string,
                schema_name=schema,
                table_filters=filter_config
            )
        self.llm = llm
        self.callbacks = callbacks or GenQueryCallbackHandler()
        # Connect to engine
        connect_args = {}
        # Only postgres accepts -csearch_path
        if self.config.connection_string.startswith("postgre"):
            connect_args['options'] = f'-csearch_path={self.config.schema_name}'
            
        self.engine = create_engine(self.config.connection_string, connect_args=connect_args)
        dialect_name = get_dialect(self.engine)
        self.validator = SecurityValidator(dialect=dialect_name)

        if custom_stages is not None:
            self.pipeline = GenQueryPipeline(stages=custom_stages)
        else:
            self.pipeline = self._build_default_pipeline()

    def _build_default_pipeline(self) -> GenQueryPipeline:
        pipeline = GenQueryPipeline()
        pipeline.add_stage(SchemaInspectorStage(self.engine, self.config, self.callbacks))
        pipeline.add_stage(SemanticRankerStage(self.llm, self.config, self.callbacks))
        pipeline.add_stage(QueryPlannerStage(self.llm, self.config, self.callbacks))
        pipeline.add_stage(QueryExecutorStage(self.llm, self.engine, self.validator, self.config, self.callbacks))
        return pipeline

    def generate(self, query: str) -> QueryResult:
        """
        Generate the SQL and Plan without executing the final query on actual data.
        It uses dry_run to ensure validation using EXPLAIN.
        """
        state = PipelineState(
            query=query, 
            context={"dry_run": False}
        )
        return self.pipeline.execute(state)

    def run(self, query: str) -> Any:
        """
        Generate SQL, plan, and execute returning the resulting DataFrame.
        """
        state = PipelineState(
            query=query, 
            context={"dry_run": False}
        )
        result = self.pipeline.execute(state)
        return result.df

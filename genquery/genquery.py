from typing import Any, Optional, Dict, List
from sqlalchemy import create_engine, event
from genquery.adapters.base import LLMAdapter
from genquery.config import GenQueryConfig, TableFilterConfig
from genquery.pipeline.pipeline import GenQueryPipeline, QueryResult
from genquery.pipeline.state import PipelineState, PipelineStage
from genquery.pipeline.inspector.inspector import SchemaInspectorStage
from genquery.pipeline.ranker.ranker import SemanticRankerStage
from genquery.pipeline.planner.planner import QueryPlannerStage
from genquery.pipeline.executor.executor import QueryExecutorStage
from genquery.pipeline.executor.validator import SecurityValidator
from genquery.core.callbacks import GenQueryCallbackHandler
from genquery.core.models import ConversationTurn
from genquery.core.utils import get_dialect

class GenQuery:
    """
    Main orchestrator class for the GenQuery system.

    Provides a facade for initializing the pipeline and executing natural
    language queries against a database using LLM adapters.
    """
    def __init__(
        self, 
        llm: LLMAdapter,
        connection_string: Optional[str] = None,
        schema: str = "public",
        config: Optional[GenQueryConfig] = None,
        connect_args: Optional[Dict[str, Any]] = None,
        table_filter: Optional[Dict[str, Any]] = None,
        config_path: Optional[str] = None,
        callbacks: Optional[GenQueryCallbackHandler] = None,
        custom_stages: Optional[List[PipelineStage]] = None
    ):
        """
        Initialize the GenQuery orchestrator.

        Args:
            llm: The LLMAdapter instance to use for generation.
            connection_string: The database connection string.
            schema: The database schema to use (default "public").
            config: A pre-configured GenQueryConfig object (takes precedence over other params).
            connect_args: Optional dictionary of keyword arguments to pass to the SQLAlchemy create_engine call.
            table_filter: Optional configuration to filter tables.
            config_path: Optional path to a YAML configuration file.
            callbacks: Optional callback handler for pipeline events.
            custom_stages: Optional list of custom pipeline stages to use instead of the default.
        """
        # Configuration resolution priority:
        # 1. Direct GenQueryConfig object
        # 2. YAML config file
        # 3. Individual parameters
        if config is not None:
            self.config = config
            if connect_args:
                self.config.connect_args = {**self.config.connect_args, **connect_args}
        elif config_path:
            self.config = GenQueryConfig.from_yaml(
                config_path,
                connection_string=connection_string,
                schema_name=schema,
                connect_args=connect_args
            )
        else:
            filter_config = TableFilterConfig(**table_filter) if table_filter else TableFilterConfig()
            self.config = GenQueryConfig(
                connection_string=connection_string,
                schema_name=schema,
                connect_args=connect_args or {},
                table_filters=filter_config
            )
        self.llm = llm
        self.callbacks = callbacks or GenQueryCallbackHandler()
        
        # Connect to engine
        engine_connect_args = self.config.connect_args.copy()

        # Only postgres accepts -csearch_path
        if self.config.connection_string and self.config.connection_string.startswith("postgre"):
            if 'options' not in engine_connect_args:
                engine_connect_args['options'] = f'-csearch_path={self.config.schema_name}'
            elif '-csearch_path' not in engine_connect_args['options']:
                engine_connect_args['options'] += f' -csearch_path={self.config.schema_name}'

        self.engine = create_engine(self.config.connection_string, connect_args=engine_connect_args)
        dialect_name = get_dialect(self.engine)

        # For Oracle: set the current schema on every connection so unqualified table names resolve correctly
        if dialect_name == "oracle" and self.config.schema_name:
            @event.listens_for(self.engine, "connect", insert=True)
            def set_oracle_schema(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute(f'ALTER SESSION SET CURRENT_SCHEMA = "{self.config.schema_name}"')
                cursor.close()

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

    def generate(
        self,
        query: str,
        conversation: Optional[List[ConversationTurn]] = None,
    ) -> QueryResult:
        """
        Generate SQL and plan for a query, optionally using previous turns as context.
        """
        state = PipelineState(
            query=query, 
            conversation=conversation or [],
            context={"dry_run": False}
        )
        return self.pipeline.execute(state)

    def run(
        self,
        query: str,
        conversation: Optional[List[ConversationTurn]] = None,
        return_result: bool = False,
    ) -> Any:
        """
        Generate SQL, plan, and execute the query.

        By default this returns the resulting DataFrame.
        Set return_result=True to receive a QueryResult containing SQL, plan, DataFrame,
        and updated conversation history for multi-turn follow-ups.
        """
        state = PipelineState(
            query=query, 
            conversation=conversation or [],
            context={"dry_run": False}
        )
        result = self.pipeline.execute(state)
        if return_result:
            return result
        return result.df

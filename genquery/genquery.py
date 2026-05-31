from typing import Any, Optional, Dict, List, Union
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
from genquery.logging import configure_logging, get_logger

logger = get_logger(__name__)

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
        custom_stages: Optional[List[PipelineStage]] = None,
        log_level: Optional[Union[str, int]] = None
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
            log_level: Optional log level override (DEBUG, INFO, WARNING, ERROR, or CRITICAL).
        """
        # Configuration resolution priority:
        # 1. Direct GenQueryConfig object
        # 2. YAML config file
        # 3. Individual parameters
        if config is not None:
            self.config = config
            if connect_args:
                self.config.connect_args = {**self.config.connect_args, **connect_args}
            if log_level is not None:
                self.config.log_level = log_level
        elif config_path:
            self.config = GenQueryConfig.from_yaml(
                config_path,
                connection_string=connection_string,
                schema_name=schema,
                connect_args=connect_args
            )
            if log_level is not None:
                self.config.log_level = log_level
        else:
            filter_config = TableFilterConfig(**table_filter) if table_filter else TableFilterConfig()
            self.config = GenQueryConfig(
                connection_string=connection_string,
                schema_name=schema,
                connect_args=connect_args or {},
                table_filters=filter_config,
                log_level=log_level or "INFO"
            )
        configure_logging(self.config.log_level)
        logger.info("Initializing GenQuery")
        logger.debug(
            "Resolved GenQuery configuration: schema=%s, row_limit=%s, stream_batch_size=%s, log_level=%s",
            self.config.schema_name,
            self.config.row_limit,
            self.config.stream_batch_size,
            self.config.log_level,
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
        logger.debug("Created SQLAlchemy engine for dialect=%s", dialect_name)

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
            logger.debug("Using %s custom pipeline stages", len(custom_stages))
        else:
            self.pipeline = self._build_default_pipeline()
        logger.info("GenQuery initialized for dialect=%s", dialect_name)

    def _build_default_pipeline(self) -> GenQueryPipeline:
        pipeline = GenQueryPipeline()
        pipeline.add_stage(SchemaInspectorStage(self.engine, self.config, self.callbacks))
        pipeline.add_stage(SemanticRankerStage(self.llm, self.config, self.callbacks))
        pipeline.add_stage(QueryPlannerStage(self.llm, self.config, self.callbacks))
        pipeline.add_stage(QueryExecutorStage(self.llm, self.engine, self.validator, self.config, self.callbacks))
        return pipeline

    def __repr__(self) -> str:
        return (
            f"GenQuery("
            f"dialect={self.engine.dialect.name}, "
            f"schema={self.config.schema_name}, "
            f"pipeline_stages={len(self.pipeline.stages)}, "
            f"llm={type(self.llm).__name__}"
            f")"
        )

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
        try:
            return self.pipeline.execute(state)
        except Exception:
            logger.exception("Failed to generate query result")
            raise

    def stream(
        self,
        query: str,
        conversation: Optional[List[ConversationTurn]] = None,
        batch_size: Optional[int] = None,
    ) -> QueryResult:
        """
        Generate SQL, plan, and return a QueryResult with a final-result stream.

        The stream yields Polars DataFrame batches, respects the configured
        row_limit, and should be consumed fully or closed explicitly. Use it as
        a context manager when you may exit iteration early:

            result = gq.stream("show orders")
            with result.stream as batches:
                for batch in batches:
                    ...
        """
        state = PipelineState(
            query=query,
            conversation=conversation or [],
            context={
                "dry_run": False,
                "stream_results": True,
                "stream_batch_size": batch_size or self.config.stream_batch_size,
            }
        )
        try:
            return self.pipeline.execute(state)
        except Exception:
            logger.exception("Failed to stream query result")
            raise

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
        try:
            result = self.pipeline.execute(state)
            logger.debug("Query execution completed")
            if return_result:
                return result
            return result.df
        except Exception:
            logger.exception("Failed to run query")
            raise

    def dry_run(
        self,
        query: str,
        conversation: Optional[List[ConversationTurn]] = None,
    ) -> QueryResult:
        """
        Generate SQL and execution plan without running the final SQL as a data query.

        Safely inspect the generated SQL and step-by-step plan before running
        the query normally. The pipeline validates the SQL by issuing an
        EXPLAIN statement against the database. Useful for debugging, review,
        or understanding how the system interprets a natural-language query.

        Args:
            query: The natural-language query to analyze.
            conversation: Optional list of prior conversation turns for context.

        Returns:
            A QueryResult containing the generated SQL, the execution plan,
            steps, and a DataFrame with the database's EXPLAIN output. The
            stream field will be None.
        """
        state = PipelineState(
            query=query,
            conversation=conversation or [],
            context={"dry_run": True}
        )
        try:
            return self.pipeline.execute(state)
        except Exception:
            logger.exception("Failed to perform dry run")
            raise

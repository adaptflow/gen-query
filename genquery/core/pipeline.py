from typing import Any, Optional, List
from sqlalchemy import create_engine
from genquery.adapters.base import LLMAdapter
from genquery.config import GenQueryConfig
from genquery.schema.inspector import SchemaInspector
from genquery.schema.ranker import SemanticRanker
from genquery.planner.planner import QueryPlanner
from genquery.executor.executor import QueryExecutor
from genquery.executor.validator import SecurityValidator
from genquery.core.callbacks import GenQueryCallbackHandler

class QueryResult:
    def __init__(self, sql: str, plan: Any, steps: Any, df: Any = None):
        self.sql = sql
        self.plan = plan
        self.steps = steps
        self.df = df

class GenQueryPipeline:
    def __init__(self, config: GenQueryConfig, llm: LLMAdapter, callbacks: Optional[GenQueryCallbackHandler] = None):
        self.config = config
        self.llm = llm
        self.callbacks = callbacks or GenQueryCallbackHandler()
        self.engine = create_engine(self.config.connection_string)
        
        self.inspector = SchemaInspector(self.engine)
        self.ranker = SemanticRanker(self.llm)
        self.planner = QueryPlanner(self.llm)
        
        # We need dialect from engine for validator
        dialect_name = self.engine.dialect.name
        self.validator = SecurityValidator(dialect=dialect_name)
        self.executor = QueryExecutor(self.llm, self.engine, self.validator, self.callbacks)

    def execute(self, query: str, dry_run: bool = False) -> QueryResult:
        # 1. Schema Inspection
        self.callbacks.on_inspector_start()
        schema_context = self.inspector.inspect(self.config.schema_name, self.config.table_filters)
        self.callbacks.on_inspector_end(len(schema_context.tables))

        # 2. Rank Tables
        self.callbacks.on_ranker_start(query)
        ranked_schema = self.ranker.rank(schema_context, query)
        self.callbacks.on_ranker_end(len(ranked_schema.tables))

        # 3. Query Plan
        self.callbacks.on_planner_start(query)
        plan = self.planner.plan(query, ranked_schema)
        self.callbacks.on_planner_end(plan)

        # 4. Generate & Execute
        df = self.executor.execute_plan(plan, ranked_schema, dry_run=dry_run)

        # Synthesize final result (for now, last step's DF)
        final_sql = self.executor.last_generated_sql
        
        return QueryResult(
            sql=final_sql,
            plan=plan,
            steps=plan.steps,
            df=df
        )

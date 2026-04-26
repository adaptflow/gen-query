import sys
from typing import Any, Dict, List, Optional
from sqlalchemy import text
from genquery.adapters.base import LLMAdapter, Message
from genquery.core.models import SchemaContext, QueryPlan, PlanStep
from genquery.pipeline.executor.validator import SecurityValidator
from genquery.pipeline.executor.result_store import ResultStore
from genquery.core.callbacks import GenQueryCallbackHandler
from genquery.pipeline.state import PipelineStage, PipelineState
from genquery.config import GenQueryConfig
from genquery.pipeline.executor.modifier import apply_security_and_limits


GENERATOR_DEFAULT_PROMPT = """
You are an expert SQL Generator. Your task is to generate ONLY a valid SQL query in {dialect} dialect for the following task:

Task: {task_description}

Available Schema:
{table_info}
{previous_context_block}
{error_context_block}
Return ONLY the raw SQL query. Do not include markdown blocks like ```sql or explanations.
"""

class ExecutionError(Exception):
    pass

class QueryExecutorStage(PipelineStage):
    """
    Stage 4: Query Generator + Executor Loop
    """
    def __init__(self, llm: LLMAdapter, engine: Any, validator: SecurityValidator, config: GenQueryConfig, callbacks: Optional[GenQueryCallbackHandler] = None):
        self.llm = llm
        self.engine = engine
        self.validator = validator
        self.config = config
        self.callbacks = callbacks or GenQueryCallbackHandler()
        self.max_retries = 3
        self.last_generated_sql = ""

    def run(self, state: PipelineState) -> PipelineState:
        schema = state.ranked_schema or state.schema_context
        dry_run = state.context.get("dry_run", False)
        
        if not state.plan:
            raise ExecutionError("QueryPlan is required for QueryExecutorStage")
            
        final_result = self.execute_plan(state.plan, schema, dry_run=dry_run)
        
        state.sql = self.last_generated_sql
        state.df = final_result
        return state

    def _generate_sql(self, step: PlanStep, schema: SchemaContext, error_context: str = "", previous_results: str = "") -> str:
        table_info = ""
        dialect = "generic"
        if schema:
            dialect = schema.dialect
            for t in schema.tables:
                table_info += f"Table: {t.name}\nColumns: {', '.join(c.name for c in t.columns)}\n\n"

        prev_block = f"\nPrevious Step Results Context:\n{previous_results}\n" if previous_results else ""
        err_block = f"\nWarning! The previous query failed with this error. Please correct your SQL:\n{error_context}\n" if error_context else ""

        prompt_template = self.config.prompts.load_prompt("generator_prompt_path", GENERATOR_DEFAULT_PROMPT)
        prompt = prompt_template.replace("{dialect}", dialect)\
                                .replace("{task_description}", step.description)\
                                .replace("{table_info}", table_info)\
                                .replace("{previous_context_block}", prev_block)\
                                .replace("{error_context_block}", err_block)

        response = self.llm.complete([Message(role="user", content=prompt)])
        
        sql = response.strip()
        if "```sql" in sql:
            sql = sql.split("```sql")[1].split("```")[0].strip()
        elif "```" in sql:
            sql = sql.split("```")[1].split("```")[0].strip()
        sql = sql.replace("\n", " ")
        return sql

    def execute_plan(self, plan: QueryPlan, schema: SchemaContext, dry_run: bool = False) -> Any:
        import polars as pl
        
        results_store = ResultStore()
        final_result = None

        for step in plan.steps:
            sql = ""
            error_context = ""
            success = False
            result_df = None
            
            # Gather previous context if dependencies exist
            prev_context = results_store.get_context(step.depends_on)

            for attempt in range(self.max_retries):
                # 1. Generate
                sql = self._generate_sql(step, schema, error_context, previous_results=prev_context)
                self.callbacks.on_sql_generated(step.id, sql)
                self.last_generated_sql = sql

                # 2. Validate
                if not self.validator.validate(sql):
                    error_context = "Query failed security validation: Only read operations (SELECT) are allowed."
                    self.callbacks.on_retry(step.id, error_context, attempt + 1)
                    continue
                
                # 3. Execute
                try:
                    with self.engine.connect() as conn:
                        # AST modification
                        sql = apply_security_and_limits(
                            sql, 
                            schema.dialect if schema else "generic", 
                            limit=self.config.row_limit,
                            rls_policies=self.config.rls_policies if schema.dialect != "postgres" else None,
                            schema=schema
                        )
                        
                        query_to_run = sql
                        if dry_run:
                            # Use EXPLAIN for dry run
                            query_to_run = f"EXPLAIN {sql}"
                            
                        # Apply Postgres explicit session variable for RLS
                        if self.config.rls_policies and schema.dialect == "postgres":
                            for policy in self.config.rls_policies:
                                if policy.session_variable:
                                    conn.execute(text(f"SET LOCAL {policy.session_variable} = '{policy.value}'"))
                            
                        # Set statement timeout
                        if schema.dialect == "postgres":
                            conn.execute(text(f"SET statement_timeout = {self.config.statement_timeout_ms}"))
                        elif schema.dialect == "mysql":
                            conn.execute(text(f"SET SESSION MAX_EXECUTION_TIME = {self.config.statement_timeout_ms}"))
                            
                        df = pl.read_database(query=query_to_run, connection=conn)
                        result_df = df
                        success = True
                        if not dry_run:
                            self.callbacks.on_execution_success(step.id, len(df))
                        break
                except Exception as e:
                    error_context = f"Database error: {str(e)}"
                    self.callbacks.on_retry(step.id, error_context, attempt + 1)
            
            if not success:
                raise ExecutionError(f"Failed to execute step {step.id} after {self.max_retries} attempts. Last error: {error_context}")
            
            # Store result
            if step.output_alias:
                results_store.save(step.output_alias, result_df)
            results_store.save(step.id, result_df)
            final_result = result_df  # Assuming sequential, last step is the final answer

        return final_result

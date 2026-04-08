import sys
from typing import Any, Dict, List, Optional
from sqlalchemy import text
from genquery.adapters.base import LLMAdapter, Message
from genquery.core.context import SchemaContext
from genquery.planner.plan_models import QueryPlan, PlanStep
from genquery.executor.validator import SecurityValidator
from genquery.executor.result_store import ResultStore
from genquery.core.callbacks import GenQueryCallbackHandler

class ExecutionError(Exception):
    pass

class QueryExecutor:
    """
    Stage 4: Query Generator + Executor Loop
    """
    def __init__(self, llm: LLMAdapter, engine: Any, validator: SecurityValidator, callbacks: Optional[GenQueryCallbackHandler] = None):
        self.llm = llm
        self.engine = engine
        self.validator = validator
        self.callbacks = callbacks or GenQueryCallbackHandler()
        self.max_retries = 3
        self.last_generated_sql = ""

    def _generate_sql(self, step: PlanStep, schema: SchemaContext, error_context: str = "", previous_results: str = "") -> str:
        table_info = ""
        for t in schema.tables:
            table_info += f"Table: {t.name}\nColumns: {', '.join(c.name for c in t.columns)}\n\n"

        prompt = f"""
You are an expert SQL Generator. Your task is to generate ONLY a valid SQL query in {schema.dialect} dialect for the following task:

Task: {step.description}

Available Schema:
{table_info}
"""
        if previous_results:
            prompt += f"\nPrevious Step Results Context:\n{previous_results}\n"
        
        if error_context:
            prompt += f"\nWarning! The previous query failed with this error. Please correct your SQL:\n{error_context}\n"

        prompt += "\nReturn ONLY the raw SQL query. Do not include markdown blocks like ```sql or explanations."

        response = self.llm.complete([Message(role="user", content=prompt)])
        sql = response.strip()
        if "```sql" in sql:
            sql = sql.split("```sql")[1].split("```")[0].strip()
        elif "```" in sql:
            sql = sql.split("```")[1].split("```")[0].strip()
        return sql

    def execute_plan(self, plan: QueryPlan, schema: SchemaContext, dry_run: bool = False) -> Any:
        import pandas as pd
        
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
                        query_to_run = sql
                        if dry_run:
                            # Use EXPLAIN for dry run
                            query_to_run = f"EXPLAIN {sql}"
                            
                        # Need to handle pandas returning None for some reason? read_sql_query always returns DF if query returns rows.
                        df = pd.read_sql_query(text(query_to_run), conn)
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

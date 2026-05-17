from typing import Any, List, Optional
from sqlalchemy import text
from genquery.adapters.base import AsyncLLMAdapter, LLMAdapter, Message

from genquery.core.models import ConversationContext, ConversationTurn, SchemaContext, QueryPlan, PlanStep
from genquery.pipeline.executor.validator import SecurityValidator
from genquery.pipeline.executor.result_store import ResultStore
from genquery.core.callbacks import AsyncGenQueryCallbackHandler, GenQueryCallbackHandler, ensure_async_callback_handler

from genquery.pipeline.state import AsyncPipelineStage, PipelineStage, PipelineState

from genquery.config import GenQueryConfig
from genquery.pipeline.executor.modifier import apply_security_and_limits


GENERATOR_DEFAULT_PROMPT = """
You are an expert SQL Generator. Your task is to generate ONLY a valid SQL query in {dialect} dialect.

Conversation context:
{conversation_context}

Current task:
{task_description}

Available Schema:
{table_info}
{previous_context_block}
{error_context_block}
Multi-turn SQL generation rules:
- If conversation context contains previous SQL and the current task is a follow-up, modify the previous SQL.
- Examples of follow-ups include "filter that to this year", "what about marketing?", "only active customers", "sort it by revenue", and "show the same thing for last quarter".
- Preserve the intent of the previous SQL unless the current task clearly changes it.
- Use only tables and columns present in the available schema.

Return ONLY the raw SQL query. Do not include markdown blocks like ```sql or explanations.
"""

def format_conversation(conversation: Optional[List[ConversationTurn]]) -> str:
    """Format recent conversation turns for SQL generation prompts."""
    return ConversationContext(turns=conversation or []).format_for_prompt()


def summarize_result(result: Any) -> Optional[str]:
    """Create a compact, prompt-safe summary of a result DataFrame."""
    if result is None:
        return None

    try:
        columns = ", ".join(result.columns)
        return f"Rows: {len(result)}; Columns: {columns}"
    except Exception:
        return None


def clean_generated_sql(response: str) -> str:
    """Strip markdown fences and normalize a raw LLM SQL response."""
    sql = response.strip()
    if "```sql" in sql:
        sql = sql.split("```sql")[1].split("```")[0].strip()
    elif "```" in sql:
        sql = sql.split("```")[1].split("```")[0].strip()
    return sql.replace("\n", " ")


def build_generator_prompt(
    config: GenQueryConfig,
    step: PlanStep,
    schema: Optional[SchemaContext],
    error_context: str = "",
    previous_results: str = "",
    conversation_context: str = "",
) -> str:
    """Build the SQL generation prompt shared by sync and async stages."""
    table_info = ""
    dialect = "generic"
    if schema:
        dialect = schema.dialect
        schema_prefix = f"{config.schema_name}." if config.schema_name and dialect == "mssql" else ""
        for table in schema.tables:
            table_info += f"Table: {schema_prefix}{table.name}\nColumns: {', '.join(column.name for column in table.columns)}\n\n"

    prev_block = f"\nPrevious Step Results Context:\n{previous_results}\n" if previous_results else ""
    err_block = f"\nWarning! The previous query failed with this error. Please correct your SQL:\n{error_context}\n" if error_context else ""

    prompt_template = config.prompts.load_prompt("generator_prompt_path", GENERATOR_DEFAULT_PROMPT)
    return prompt_template.replace("{dialect}", dialect)\
                          .replace("{task_description}", step.description)\
                          .replace("{table_info}", table_info)\
                          .replace("{previous_context_block}", prev_block)\
                          .replace("{error_context_block}", err_block)\
                          .replace("{conversation_context}", conversation_context or "No previous conversation.")


def apply_query_modifiers(sql: str, schema: SchemaContext, config: GenQueryConfig) -> str:
    """Apply SQL security and limit modifiers shared by sync and async executors."""
    return apply_security_and_limits(
        sql,
        'tsql' if schema.dialect == "mssql" else schema.dialect,
        limit=config.row_limit,
        rls_policies=config.rls_policies if schema.dialect != "postgres" else None,
        schema=schema
    )


def build_timeout_statement(dialect: str, timeout_ms: int) -> Optional[str]:
    """Return a dialect-specific timeout statement when SQLAlchemy can execute one directly."""
    if dialect == "postgres":
        return f"SET statement_timeout = {timeout_ms}"
    if dialect == "mysql":
        return f"SET SESSION MAX_EXECUTION_TIME = {timeout_ms}"
    if dialect == "mssql":
        return f"SET LOCK_TIMEOUT {timeout_ms}"
    return None


class ExecutionError(Exception):
    """Exception raised for errors during query execution."""
    pass


class QueryExecutorStage(PipelineStage):
    """
    Stage 4: Query Generator + Executor Loop
    """
    def __init__(self, llm: LLMAdapter, engine: Any, validator: SecurityValidator, config: GenQueryConfig, callbacks: Optional[GenQueryCallbackHandler] = None):
        """Initialize the QueryExecutorStage."""
        self.llm = llm
        self.engine = engine
        self.validator = validator
        self.config = config
        self.callbacks = callbacks or GenQueryCallbackHandler()
        self.max_retries = 3
        self.last_generated_sql = ""

    def run(self, state: PipelineState) -> PipelineState:
        """Run the execution stage to generate and execute SQL."""
        schema = state.ranked_schema or state.schema_context
        dry_run = state.context.get("dry_run", False)
        
        if not state.plan:
            raise ExecutionError("QueryPlan is required for QueryExecutorStage")
            
        conversation_context = format_conversation(state.conversation)
        final_result = self.execute_plan(
            state.plan,
            schema,
            dry_run=dry_run,
            conversation_context=conversation_context,
        )
        
        state.sql = self.last_generated_sql
        state.df = final_result
        state.conversation.append(
            ConversationTurn(
                user_query=state.query,
                sql=state.sql,
                plan=state.plan.model_dump() if state.plan else None,
                result_summary=summarize_result(final_result),
            )
        )
        return state

    def _generate_sql(
        self,
        step: PlanStep,
        schema: SchemaContext,
        error_context: str = "",
        previous_results: str = "",
        conversation_context: str = "",
    ) -> str:
        prompt = build_generator_prompt(
            self.config,
            step,
            schema,
            error_context=error_context,
            previous_results=previous_results,
            conversation_context=conversation_context,
        )
        response = self.llm.complete([Message(role="user", content=prompt)])
        return clean_generated_sql(response)

    def execute_plan(
        self,
        plan: QueryPlan,
        schema: SchemaContext,
        dry_run: bool = False,
        conversation_context: str = "",
    ) -> Any:
        """Execute the query plan and return the result DataFrame."""
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
                sql = self._generate_sql(
                    step,
                    schema,
                    error_context,
                    previous_results=prev_context,
                    conversation_context=conversation_context,
                )
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
                        sql = apply_query_modifiers(sql, schema, self.config)
                        query_to_run = f"EXPLAIN {sql}" if dry_run else sql
                            
                        # Apply Postgres explicit session variable for RLS
                        if self.config.rls_policies and schema.dialect == "postgres":
                            for policy in self.config.rls_policies:
                                if policy.session_variable:
                                    conn.execute(text(f"SET LOCAL {policy.session_variable} = '{policy.value}'"))
                            
                        # Set statement timeout when the dialect supports a direct SET command.
                        timeout_statement = build_timeout_statement(schema.dialect, self.config.statement_timeout_ms)
                        if timeout_statement:
                            conn.execute(text(timeout_statement))
                            
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

class AsyncQueryExecutorStage(AsyncPipelineStage):
    """
    Async Stage 4: Query Generator + Executor Loop.
    """
    def __init__(self, llm: AsyncLLMAdapter, engine: Any, validator: SecurityValidator, config: GenQueryConfig, callbacks: Optional[AsyncGenQueryCallbackHandler] = None):
        self.llm = llm
        self.engine = engine
        self.validator = validator
        self.config = config
        self.callbacks = ensure_async_callback_handler(callbacks)

        self.max_retries = 3
        self.last_generated_sql = ""

    async def run(self, state: PipelineState) -> PipelineState:
        schema = state.ranked_schema or state.schema_context
        dry_run = state.context.get("dry_run", False)

        if not state.plan:
            raise ExecutionError("QueryPlan is required for AsyncQueryExecutorStage")
        if not schema:
            raise ExecutionError("SchemaContext is required for AsyncQueryExecutorStage")

        conversation_context = format_conversation(state.conversation)
        final_result = await self.execute_plan(
            state.plan,
            schema,
            dry_run=dry_run,
            conversation_context=conversation_context,
        )

        state.sql = self.last_generated_sql
        state.df = final_result
        state.conversation.append(
            ConversationTurn(
                user_query=state.query,
                sql=state.sql,
                plan=state.plan.model_dump() if state.plan else None,
                result_summary=summarize_result(final_result),
            )
        )
        return state

    async def _generate_sql(
        self,
        step: PlanStep,
        schema: SchemaContext,
        error_context: str = "",
        previous_results: str = "",
        conversation_context: str = "",
    ) -> str:
        prompt = build_generator_prompt(
            self.config,
            step,
            schema,
            error_context=error_context,
            previous_results=previous_results,
            conversation_context=conversation_context,
        )
        response = await self.llm.acomplete([Message(role="user", content=prompt)])
        return clean_generated_sql(response)

    async def execute_plan(
        self,
        plan: QueryPlan,
        schema: SchemaContext,
        dry_run: bool = False,
        conversation_context: str = "",
    ) -> Any:
        import polars as pl

        results_store = ResultStore()
        final_result = None

        for step in plan.steps:
            error_context = ""
            success = False
            result_df = None
            prev_context = results_store.get_context(step.depends_on)

            for attempt in range(self.max_retries):
                sql = await self._generate_sql(
                    step,
                    schema,
                    error_context,
                    previous_results=prev_context,
                    conversation_context=conversation_context,
                )
                await self.callbacks.aon_sql_generated(step.id, sql)
                self.last_generated_sql = sql

                if not self.validator.validate(sql):
                    error_context = "Query failed security validation: Only read operations (SELECT) are allowed."
                    await self.callbacks.aon_retry(step.id, error_context, attempt + 1)
                    continue

                try:
                    sql = apply_query_modifiers(sql, schema, self.config)
                    query_to_run = f"EXPLAIN {sql}" if dry_run else sql

                    async with self.engine.connect() as conn:
                        async with conn.begin():
                            if self.config.rls_policies and schema.dialect == "postgres":
                                for policy in self.config.rls_policies:
                                    if policy.session_variable:
                                        await conn.execute(text(f"SET LOCAL {policy.session_variable} = '{policy.value}'"))

                            timeout_statement = build_timeout_statement(schema.dialect, self.config.statement_timeout_ms)
                            if timeout_statement:
                                await conn.execute(text(timeout_statement))

                            result = await conn.execute(text(query_to_run))
                            columns = list(result.keys())
                            rows = [dict(row) for row in result.mappings().all()]
                            result_df = pl.DataFrame(rows) if rows else pl.DataFrame({column: [] for column in columns})


                    success = True
                    if not dry_run:
                        await self.callbacks.aon_execution_success(step.id, len(result_df))
                    break
                except Exception as e:
                    error_context = f"Database error: {str(e)}"
                    await self.callbacks.aon_retry(step.id, error_context, attempt + 1)

            if not success:
                raise ExecutionError(f"Failed to execute step {step.id} after {self.max_retries} attempts. Last error: {error_context}")

            if step.output_alias:
                results_store.save(step.output_alias, result_df)
            results_store.save(step.id, result_df)
            final_result = result_df

        return final_result


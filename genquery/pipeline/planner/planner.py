import json
from typing import List, Optional
from genquery.adapters.base import AsyncLLMAdapter, LLMAdapter, Message

from genquery.core.models import ConversationContext, ConversationTurn, SchemaContext, QueryPlan
from genquery.pipeline.state import AsyncPipelineStage, PipelineStage, PipelineState
from genquery.core.callbacks import AsyncGenQueryCallbackHandler, GenQueryCallbackHandler, ensure_async_callback_handler


from genquery.config import GenQueryConfig


PLANNER_DEFAULT_PROMPT = """
You are an expert database architect. You must generate an execution plan for a user's natural language query.
The SQL dialect is: {dialect}.

Conversation context:
{conversation_context}

Current user query: {query}

Available Schema:
{table_info}

Important multi-turn instructions:
- The current query may be a follow-up to the prior conversation.
- If the user says things like "that", "those", "now filter", "what about", or "only this year", infer the reference from previous queries and SQL.
- If the current query modifies the previous request, produce a plan that updates or extends the previous SQL intent.
- Do not ignore the current query.
- Do not blindly reuse previous SQL if the current query asks a new question.

Create a structured plan. The output must be valid JSON matching this schema:
{{
  "strategy": "single" | "sequential" | "parallel",
  "steps": [
    {{
      "id": "step_1",
      "description": "Describe what this step does",
      "depends_on": ["id_of_previous_step"],
      "output_alias": "temp_result_name",
      "receives_context": "temp_result_name"
    }}
  ]
}}

Return ONLY the JSON object.
"""


def format_conversation(conversation: Optional[List[ConversationTurn]]) -> str:
    """Format recent conversation turns for planner/ranker/executor prompts."""
    return ConversationContext(turns=conversation or []).format_for_prompt()


def build_planner_prompt(
    config: GenQueryConfig,
    query: str,
    schema: Optional[SchemaContext],
    conversation: Optional[List[ConversationTurn]] = None,
) -> str:
    """Build the planner prompt shared by sync and async stages."""
    table_info = ""
    dialect = "generic"

    if schema:
        dialect = schema.dialect
        for table in schema.tables:
            table_info += f"Table: {table.name}\nColumns: {', '.join(column.name for column in table.columns)}\n\n"

    prompt_template = config.prompts.load_prompt("planner_prompt_path", PLANNER_DEFAULT_PROMPT)
    return prompt_template.replace("{query}", query)\
                          .replace("{table_info}", table_info)\
                          .replace("{dialect}", dialect)\
                          .replace("{conversation_context}", format_conversation(conversation))


def parse_planner_response(response: str, fallback_query: str) -> QueryPlan:
    """Parse an LLM planner response, falling back to a single-step plan."""
    try:
        content = response.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        plan_data = json.loads(content)
        return QueryPlan(**plan_data)
    except Exception:
        return QueryPlan(
            strategy="single",
            steps=[
                {
                    "id": "step_1",
                    "description": fallback_query,
                    "depends_on": []
                }
            ]
        )


class QueryPlannerStage(PipelineStage):
    """
    Stage 3: Query Planner (Agentic).
    """
    def __init__(self, llm: LLMAdapter, config: GenQueryConfig, callbacks: Optional[GenQueryCallbackHandler] = None):
        """Initialize the query planner stage."""
        self.llm = llm
        self.config = config
        self.callbacks = callbacks or GenQueryCallbackHandler()

    def run(self, state: PipelineState) -> PipelineState:
        """Run the planner stage to generate a query execution plan."""
        self.callbacks.on_planner_start(state.query)
        schema = state.ranked_schema or state.schema_context
        
        plan = self.plan(state.query, schema, conversation=state.conversation)
        state.plan = plan
        
        self.callbacks.on_planner_end(plan)
        return state

    def plan(
        self,
        query: str,
        schema: SchemaContext,
        conversation: Optional[List[ConversationTurn]] = None,
    ) -> QueryPlan:
        """Generate a query plan using the LLM based on the query, schema, and conversation."""
        prompt = build_planner_prompt(self.config, query, schema, conversation)
        response = self.llm.complete([Message(role="user", content=prompt)])
        return parse_planner_response(response, query)

class AsyncQueryPlannerStage(AsyncPipelineStage):
    """
    Async Stage 3: Query Planner (Agentic).
    """
    def __init__(self, llm: AsyncLLMAdapter, config: GenQueryConfig, callbacks: Optional[AsyncGenQueryCallbackHandler] = None):
        self.llm = llm
        self.config = config
        self.callbacks = ensure_async_callback_handler(callbacks)


    async def run(self, state: PipelineState) -> PipelineState:
        await self.callbacks.aon_planner_start(state.query)
        schema = state.ranked_schema or state.schema_context

        plan = await self.plan(state.query, schema, conversation=state.conversation)
        state.plan = plan

        await self.callbacks.aon_planner_end(plan)
        return state

    async def plan(
        self,
        query: str,
        schema: SchemaContext,
        conversation: Optional[List[ConversationTurn]] = None,
    ) -> QueryPlan:
        prompt = build_planner_prompt(self.config, query, schema, conversation)
        response = await self.llm.acomplete([Message(role="user", content=prompt)])
        return parse_planner_response(response, query)



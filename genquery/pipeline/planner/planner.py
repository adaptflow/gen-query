import json
from typing import List, Optional
from genquery.adapters.base import LLMAdapter, Message
from genquery.core.models import ConversationContext, ConversationTurn, SchemaContext, QueryPlan
from genquery.pipeline.state import PipelineStage, PipelineState
from genquery.core.callbacks import GenQueryCallbackHandler
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

    def _format_conversation(self, conversation: Optional[List[ConversationTurn]]) -> str:
        """Format recent conversation turns for the planner prompt."""
        return ConversationContext(turns=conversation or []).format_for_prompt()

    def plan(
        self,
        query: str,
        schema: SchemaContext,
        conversation: Optional[List[ConversationTurn]] = None,
    ) -> QueryPlan:
        """Generate a query plan using the LLM based on the query, schema, and conversation."""
        table_info = ""
        dialect = "generic"
        
        if schema:
            dialect = schema.dialect
            for t in schema.tables:
                table_info += f"Table: {t.name}\nColumns: {', '.join(c.name for c in t.columns)}\n\n"

        prompt_template = self.config.prompts.load_prompt("planner_prompt_path", PLANNER_DEFAULT_PROMPT)
        prompt = prompt_template.replace("{query}", query)\
                                .replace("{table_info}", table_info)\
                                .replace("{dialect}", dialect)\
                                .replace("{conversation_context}", self._format_conversation(conversation))

        response = self.llm.complete([Message(role="user", content=prompt)])
        try:
            content = response.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            plan_data = json.loads(content)
            return QueryPlan(**plan_data)
        except Exception as e:
            # Fallback to a single step plan
            return QueryPlan(
                strategy="single",
                steps=[
                    {
                        "id": "step_1",
                        "description": query,
                        "depends_on": []
                    }
                ]
            )

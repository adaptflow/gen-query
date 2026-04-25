import json
from typing import Optional
from genquery.adapters.base import LLMAdapter, Message
from genquery.core.context import SchemaContext
from genquery.planner.plan_models import QueryPlan
from genquery.core.state import PipelineStage, PipelineState
from genquery.core.callbacks import GenQueryCallbackHandler
from genquery.config import GenQueryConfig


PLANNER_DEFAULT_PROMPT = """
You are an expert database architect. You must generate an execution plan for a user's natural language query.
The SQL dialect is: {dialect}.

User query: {query}

Available Schema:
{table_info}

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
        self.llm = llm
        self.config = config
        self.callbacks = callbacks or GenQueryCallbackHandler()

    def run(self, state: PipelineState) -> PipelineState:
        self.callbacks.on_planner_start(state.query)
        schema = state.ranked_schema or state.schema_context
        
        plan = self.plan(state.query, schema)
        state.plan = plan
        
        self.callbacks.on_planner_end(plan)
        return state

    def plan(self, query: str, schema: SchemaContext) -> QueryPlan:
        table_info = ""
        dialect = "generic"
        
        if schema:
            dialect = schema.dialect
            for t in schema.tables:
                table_info += f"Table: {t.name}\nColumns: {', '.join(c.name for c in t.columns)}\n\n"

        prompt_template = self.config.prompts.load_prompt("planner_prompt_path", PLANNER_DEFAULT_PROMPT)
        prompt = prompt_template.replace("{query}", query).replace("{table_info}", table_info).replace("{dialect}", dialect)

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

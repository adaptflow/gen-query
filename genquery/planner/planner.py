import json
from genquery.adapters.base import LLMAdapter, Message
from genquery.core.context import SchemaContext
from genquery.planner.plan_models import QueryPlan

class QueryPlanner:
    """
    Stage 3: Query Planner (Agentic).
    """
    def __init__(self, llm: LLMAdapter):
        self.llm = llm

    def plan(self, query: str, schema: SchemaContext) -> QueryPlan:
        table_info = ""
        for t in schema.tables:
            table_info += f"Table: {t.name}\nColumns: {', '.join(c.name for c in t.columns)}\n\n"

        prompt = f"""
You are an expert database architect. You must generate an execution plan for a user's natural language query.
The SQL dialect is: {schema.dialect}.

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

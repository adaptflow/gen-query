import json
from typing import List, Optional
from genquery.adapters.base import LLMAdapter, Message
from genquery.core.context import SchemaContext, TableMetadata
from genquery.core.state import PipelineStage, PipelineState
from genquery.core.callbacks import GenQueryCallbackHandler
from genquery.config import GenQueryConfig

RANKER_DEFAULT_PROMPT = """
Given the following database tables, identify the most relevant tables needed to answer the user's query.
Return *only* a JSON array of strings containing the table names, up to {top_k} tables.

User query: {query}

Tables:
{table_info}
"""

class SemanticRankerStage(PipelineStage):
    """
    Stage 2: Semantic Table Ranker.
    Determines the most relevant tables for the given NL query.
    """
    def __init__(self, llm: LLMAdapter, config: GenQueryConfig, callbacks: Optional[GenQueryCallbackHandler] = None):
        self.llm = llm
        self.config = config
        self.callbacks = callbacks or GenQueryCallbackHandler()

    def run(self, state: PipelineState) -> PipelineState:
        self.callbacks.on_ranker_start(state.query)
        
        schema = state.schema_context
        # If no schema is available, just pass it through
        if not schema:
            state.ranked_schema = None
            self.callbacks.on_ranker_end(0)
            return state
            
        ranked_schema = self.rank(schema, state.query)
        state.ranked_schema = ranked_schema
        
        self.callbacks.on_ranker_end(len(ranked_schema.tables))
        return state

    def rank(self, schema: SchemaContext, query: str, top_k: int = 5) -> SchemaContext:
        if len(schema.tables) <= top_k:
            return schema

        table_info = ""
        for t in schema.tables:
            table_info += f"- Table: {t.name}\n"
            if t.description:
                table_info += f"  Description: {t.description}\n"

        # Load from config or use default
        prompt_template = self.config.prompts.load_prompt("ranker_prompt_path", RANKER_DEFAULT_PROMPT)
        prompt = prompt_template.replace("{query}", query).replace("{table_info}", table_info).replace("{top_k}", str(top_k))

        response = self.llm.complete([Message(role="user", content=prompt)])
        
        try:
            content = response.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            relevant_names = json.loads(content)
            filtered_tables = [t for t in schema.tables if t.name in relevant_names]
            return SchemaContext(tables=filtered_tables, dialect=schema.dialect)
        except Exception:
            return SchemaContext(tables=schema.tables[:top_k], dialect=schema.dialect)

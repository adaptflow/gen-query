import json
from typing import List
from genquery.adapters.base import LLMAdapter, Message
from genquery.core.context import SchemaContext, TableMetadata

class SemanticRanker:
    """
    Stage 2: Semantic Table Ranker.
    Determines the most relevant tables for the given NL query.
    """
    def __init__(self, llm: LLMAdapter):
        self.llm = llm

    def rank(self, schema: SchemaContext, query: str, top_k: int = 5) -> SchemaContext:
        if len(schema.tables) <= top_k:
            return schema

        table_info = ""
        for t in schema.tables:
            table_info += f"- Table: {t.name}\n  Columns: {', '.join(c.name for c in t.columns)}\n"
            if t.description:
                table_info += f"  Description: {t.description}\n"

        prompt = f"""
Given the following database tables, identify the most relevant tables needed to answer the user's query.
Return *only* a JSON array of strings containing the table names, up to {top_k} tables.

User query: {query}

Tables:
{table_info}
"""
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

import json
from typing import List, Optional
from genquery.adapters.base import AsyncLLMAdapter, LLMAdapter, Message

from genquery.core.models import ConversationContext, ConversationTurn, SchemaContext

from genquery.pipeline.state import AsyncPipelineStage, PipelineStage, PipelineState

from genquery.core.callbacks import AsyncGenQueryCallbackHandler, GenQueryCallbackHandler, ensure_async_callback_handler


from genquery.config import GenQueryConfig

RANKER_DEFAULT_PROMPT = """
Given the following database tables, identify the most relevant tables needed to answer the user's query.
Return *only* a JSON array of strings containing the table names, up to {top_k} tables.

Conversation context:
{conversation_context}

Current user query: {query}

Important multi-turn instructions:
- The current query may be a follow-up that references prior tables or SQL using words like "that", "those", "now", or "what about".
- Use the conversation context to keep tables that were relevant to previous turns when the current query is ambiguous.

Tables:
{table_info}
"""


def format_conversation(conversation: Optional[List[ConversationTurn]]) -> str:
    """Format recent conversation turns for ranker prompts."""
    return ConversationContext(turns=conversation or []).format_for_prompt()


def build_ranker_prompt(
    config: GenQueryConfig,
    schema: SchemaContext,
    query: str,
    top_k: int,
    conversation: Optional[List[ConversationTurn]] = None,
) -> str:
    """Build the ranker prompt shared by sync and async stages."""
    table_info = ""
    for table in schema.tables:
        table_info += f"- Table: {table.name}\n"
        if table.description:
            table_info += f"  Description: {table.description}\n"

    prompt_template = config.prompts.load_prompt("ranker_prompt_path", RANKER_DEFAULT_PROMPT)
    return prompt_template.replace("{query}", query)\
                          .replace("{table_info}", table_info)\
                          .replace("{top_k}", str(top_k))\
                          .replace("{conversation_context}", format_conversation(conversation))


def parse_ranker_response(response: str, schema: SchemaContext, top_k: int) -> SchemaContext:
    """Parse an LLM ranker response, falling back to the first top_k tables."""
    try:
        content = response.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        relevant_names = json.loads(content)
        filtered_tables = [table for table in schema.tables if table.name in relevant_names]
        return SchemaContext(tables=filtered_tables, dialect=schema.dialect)
    except Exception:
        return SchemaContext(tables=schema.tables[:top_k], dialect=schema.dialect)


class SemanticRankerStage(PipelineStage):
    """
    Stage 2: Semantic Table Ranker.
    Determines the most relevant tables for the given NL query.
    """
    def __init__(self, llm: LLMAdapter, config: GenQueryConfig, callbacks: Optional[GenQueryCallbackHandler] = None):
        """Initialize the semantic ranker stage."""
        self.llm = llm
        self.config = config
        self.callbacks = callbacks or GenQueryCallbackHandler()

    def run(self, state: PipelineState) -> PipelineState:
        """Run the ranker stage to filter and rank schema tables."""
        self.callbacks.on_ranker_start(state.query)
        
        schema = state.schema_context
        # If no schema is available, just pass it through
        if not schema:
            state.ranked_schema = None
            self.callbacks.on_ranker_end(0)
            return state
            
        ranked_schema = self.rank(schema, state.query, conversation=state.conversation)
        state.ranked_schema = ranked_schema
        
        self.callbacks.on_ranker_end(len(ranked_schema.tables))
        return state

    def rank(
        self,
        schema: SchemaContext,
        query: str,
        top_k: int = 5,
        conversation: Optional[List[ConversationTurn]] = None,
    ) -> SchemaContext:
        """Rank and return the top-k most relevant tables from the schema for the given query."""
        if len(schema.tables) <= top_k:
            return schema

        prompt = build_ranker_prompt(self.config, schema, query, top_k, conversation)
        response = self.llm.complete([Message(role="user", content=prompt)])
        return parse_ranker_response(response, schema, top_k)



class AsyncSemanticRankerStage(AsyncPipelineStage):
    """
    Async Stage 2: Semantic Table Ranker.
    """
    def __init__(self, llm: AsyncLLMAdapter, config: GenQueryConfig, callbacks: Optional[AsyncGenQueryCallbackHandler] = None):



        self.llm = llm
        self.config = config
        self.callbacks = ensure_async_callback_handler(callbacks)


    async def run(self, state: PipelineState) -> PipelineState:
        await self.callbacks.aon_ranker_start(state.query)

        schema = state.schema_context
        if not schema:
            state.ranked_schema = None
            await self.callbacks.aon_ranker_end(0)
            return state

        ranked_schema = await self.rank(schema, state.query, conversation=state.conversation)
        state.ranked_schema = ranked_schema

        await self.callbacks.aon_ranker_end(len(ranked_schema.tables))
        return state

    async def rank(
        self,
        schema: SchemaContext,
        query: str,
        top_k: int = 5,
        conversation: Optional[List[ConversationTurn]] = None,
    ) -> SchemaContext:
        if len(schema.tables) <= top_k:
            return schema

        prompt = build_ranker_prompt(self.config, schema, query, top_k, conversation)
        response = await self.llm.acomplete([Message(role="user", content=prompt)])
        return parse_ranker_response(response, schema, top_k)

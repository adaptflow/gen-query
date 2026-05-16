from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class ConversationTurn(BaseModel):
    """A prior natural-language query and its generated artifacts for multi-turn context."""
    user_query: str
    sql: Optional[str] = None
    plan: Optional[Dict[str, Any]] = None
    result_summary: Optional[str] = None

class ConversationContext(BaseModel):
    """A portable conversation history passed between GenQuery calls."""
    turns: List[ConversationTurn] = []

    def format_for_prompt(self, max_turns: int = 3) -> str:
        """Render recent conversation turns for LLM prompts."""
        recent_turns = self.turns[-max_turns:]
        if not recent_turns:
            return "No previous conversation."

        blocks = []
        for index, turn in enumerate(recent_turns, start=1):
            blocks.append(
                f"Turn {index}:\n"
                f"User query: {turn.user_query}\n"
                f"Generated SQL: {turn.sql or 'N/A'}\n"
                f"Result summary: {turn.result_summary or 'N/A'}"
            )
        return "\n\n".join(blocks)

class ColumnMetadata(BaseModel):
    """Metadata representing a database table column."""
    name: str
    type: str
    primary_key: bool
    nullable: bool

class IndexMetadata(BaseModel):
    """Metadata representing a database index."""
    name: str
    column_names: List[str]
    unique: bool

class TableMetadata(BaseModel):
    """Metadata representing a database table."""
    name: str
    description: Optional[str] = None
    columns: List[ColumnMetadata]
    foreign_keys: List[Dict[str, Any]] = []
    indexes: List[IndexMetadata] = []

class SchemaContext(BaseModel):
    """Contextual representation of the database schema."""
    tables: List[TableMetadata]
    dialect: str

class PlanStep(BaseModel):
    """A single step within a query execution plan."""
    id: str
    description: str
    depends_on: List[str] = []
    output_alias: Optional[str] = None
    receives_context: Optional[str] = None

class QueryPlan(BaseModel):
    """A complete query execution plan."""
    strategy: str  # "single", "sequential", "parallel"
    steps: List[PlanStep]

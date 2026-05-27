import asyncio

from genquery.config import GenQueryConfig
from genquery.core.models import ColumnMetadata, ConversationTurn, SchemaContext, TableMetadata
from genquery.pipeline.planner.planner import (
    build_planner_prompt,
    format_conversation as format_planner_conversation,
    parse_planner_response,
)
from genquery.pipeline.ranker.ranker import (
    SemanticRankerStage,
    build_ranker_prompt,
    format_conversation as format_ranker_conversation,
    parse_ranker_response,
)


class RecordingLLM:
    def __init__(self, response: str):
        self.response = response
        self.calls = []

    def complete(self, messages, **kwargs):
        self.calls.append(messages)
        return self.response


class AsyncRecordingLLM:
    def __init__(self, response: str):
        self.response = response
        self.calls = []

    async def acomplete(self, messages, **kwargs):
        self.calls.append(messages)
        return self.response


def make_schema(table_count: int = 6) -> SchemaContext:
    return SchemaContext(
        dialect="sqlite",
        tables=[
            TableMetadata(
                name=f"table_{index}",
                description=f"Description {index}",
                columns=[
                    ColumnMetadata(name="id", type="INTEGER", primary_key=True, nullable=False),
                    ColumnMetadata(name="value", type="TEXT", primary_key=False, nullable=True),
                ],
            )
            for index in range(table_count)
        ],
    )


def test_ranker_response_parses_fenced_json_and_filters_unknown_tables():
    schema = make_schema()

    ranked = parse_ranker_response('```json\n["table_3", "missing", "table_1"]\n```', schema, top_k=5)

    assert [table.name for table in ranked.tables] == ["table_1", "table_3"]
    assert ranked.dialect == "sqlite"


def test_ranker_response_falls_back_to_first_top_k_tables_for_invalid_json():
    schema = make_schema()

    ranked = parse_ranker_response("not json", schema, top_k=2)

    assert [table.name for table in ranked.tables] == ["table_0", "table_1"]


def test_semantic_ranker_skips_llm_when_schema_is_already_small():
    schema = make_schema(table_count=2)
    llm = RecordingLLM('["table_1"]')
    stage = SemanticRankerStage(llm, GenQueryConfig(connection_string="sqlite://"))

    ranked = stage.rank(schema, "Find values", top_k=5)

    assert ranked is schema
    assert llm.calls == []


def test_semantic_ranker_calls_llm_for_larger_schema():
    schema = make_schema(table_count=6)
    llm = RecordingLLM('["table_4"]')
    stage = SemanticRankerStage(llm, GenQueryConfig(connection_string="sqlite://"))

    ranked = stage.rank(schema, "Find values", top_k=5)

    assert [table.name for table in ranked.tables] == ["table_4"]
    assert len(llm.calls) == 1
    assert "Find values" in llm.calls[0][0].content


def test_planner_response_parses_fenced_json():
    response = """
    ```json
    {
      "strategy": "sequential",
      "steps": [
        {"id": "step_1", "description": "Get rows", "output_alias": "rows"},
        {"id": "step_2", "description": "Summarize", "depends_on": ["step_1"]}
      ]
    }
    ```
    """

    plan = parse_planner_response(response, fallback_query="fallback")

    assert plan.strategy == "sequential"
    assert [step.id for step in plan.steps] == ["step_1", "step_2"]
    assert plan.steps[0].output_alias == "rows"
    assert plan.steps[1].depends_on == ["step_1"]


def test_planner_response_falls_back_to_single_step_plan_for_invalid_json():
    plan = parse_planner_response("not json", fallback_query="Show users")

    assert plan.strategy == "single"
    assert len(plan.steps) == 1
    assert plan.steps[0].id == "step_1"
    assert plan.steps[0].description == "Show users"
    assert plan.steps[0].depends_on == []


def test_conversation_formatters_include_recent_turns_and_omit_older_turns():
    turns = [
        ConversationTurn(user_query=f"query {index}", sql=f"SELECT {index}", result_summary=f"Rows: {index}")
        for index in range(4)
    ]

    formatted = format_ranker_conversation(turns)

    assert "query 0" not in formatted
    assert "query 1" in formatted
    assert "SELECT 3" in formatted
    assert format_planner_conversation([]) == "No previous conversation."


def test_ranker_and_planner_prompts_include_schema_query_and_conversation_context():
    config = GenQueryConfig(connection_string="sqlite://")
    schema = make_schema(table_count=1)
    conversation = [ConversationTurn(user_query="previous", sql="SELECT * FROM table_0")]

    ranker_prompt = build_ranker_prompt(config, schema, "current", top_k=3, conversation=conversation)
    planner_prompt = build_planner_prompt(config, "current", schema, conversation=conversation)

    assert "current" in ranker_prompt
    assert "table_0" in ranker_prompt
    assert "up to 3 tables" in ranker_prompt
    assert "previous" in ranker_prompt
    assert "sqlite" in planner_prompt
    assert "Columns: id, value" in planner_prompt
    assert "previous" in planner_prompt


def test_async_llm_test_double_can_be_used_by_async_parsers_callers():
    async def call_llm():
        llm = AsyncRecordingLLM('{"strategy":"single","steps":[{"id":"s","description":"d"}]}')
        response = await llm.acomplete([])
        return parse_planner_response(response, fallback_query="fallback"), llm.calls

    plan, calls = asyncio.run(call_llm())

    assert plan.steps[0].id == "s"
    assert calls == [[]]

# GenQuery

GenQuery is an agentic, highly customizable Natural Language to SQL generation and execution framework. It converts natural language queries into executable SQL, validates security, executes the queries against your database, and returns results as DataFrames.

## Key Features

- **Agentic Pipeline**: Broken down into discrete, customizable stages (Inspector, Ranker, Planner, Executor).
- **Multi-LLM Support**: Built-in adapters for OpenAI, Anthropic, Gemini, LangChain, and Ollama local models.
- **Security-First**: Enforces strictly read-only (`SELECT`) queries via AST validation and injects Row-Level Security (RLS) policies dynamically.
- **Enterprise Scale**: Includes semantic table ranking to avoid context limits, execution plans for complex queries, and schema caching.
- **Customizable**: Swap out any pipeline stage to fit your specific needs or integrate with your own systems.

## Architecture

The system operates on a 4-stage pipeline by default:
1. **Schema Inspector**: Connects to the database via SQLAlchemy, extracts schema metadata, and caches it.
2. **Semantic Ranker**: Uses an LLM to identify and rank only the relevant tables for the user's query, reducing context overhead.
3. **Query Planner**: Breaks the natural language request down into a logical execution plan (single step, sequential, etc.).
4. **Query Executor**: Generates SQL for each step in the plan, applies AST-based security limits and validations, executes the queries safely, and returns a Polars DataFrame.

## Installation

Ensure you have the required dependencies. You'll generally need `sqlalchemy`, `polars`, `pydantic`, `sqlglot`, and the SDK for your preferred LLM.

```bash
pip install sqlalchemy polars pydantic sqlglot pyyaml requests
# Plus your LLM provider of choice:
# pip install openai anthropic google-generativeai langchain
```

## Quick Start

```python
from genquery import GenQuery
from genquery.adapters.openai_adapter import OpenAIAdapter

# 1. Initialize your LLM adapter
llm = OpenAIAdapter(api_key="sk-...", model="gpt-5.5")


# 2. Setup GenQuery (multiple configuration options)

# Option A: Simple setup with individual parameters
gq = GenQuery(
    llm=llm,
    connection_string="postgresql://user:pass@localhost:5432/mydb",
    schema="public"
)

# Option B: Using a pre-configured GenQueryConfig object
from genquery.config import GenQueryConfig, TableFilterConfig, RLSPolicy

config = GenQueryConfig(
    connection_string="postgresql://user:pass@localhost:5432/mydb",
    schema_name="public",
    connect_args={"connect_timeout": 10},
    table_filters=TableFilterConfig(exclude=["migrations", "audit_logs"]),
    statement_timeout_ms=10000,
    row_limit=100,
    rls_policies=[RLSPolicy(column="tenant_id", value="t-12345")]
)
gq = GenQuery(llm=llm, config=config)

# Option C: Using a YAML configuration file
gq = GenQuery(llm=llm, config_path="config.yaml")

# 3. Run a query!
df = gq.run("Show me the top 5 customers by total order amount this year")
print(df)
```

## Supported LLMs

GenQuery includes out-of-the-box adapters for popular models:
- `OpenAIAdapter` (GPT)
- `AnthropicAdapter` (Claude)
- `GeminiAdapter` (Gemini)
- `OllamaAdapter` (Local models)
- `LangChainAdapter` (Wrap any LangChain BaseChatModel)

## Tested databases

- `postgres`

## Configuration & Security

You can configure GenQuery via code or a YAML file to enforce table filters, row limits, statement timeouts, and Row-Level Security (RLS).

### Read-Only Enforcement
All generated SQL is validated using AST parsing to ensure it contains only `SELECT` statements. `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, and other destructive operations are rejected.

### Row-Level Security (RLS)
The executor can parse the generated AST and inject `WHERE` clauses for specific tables dynamically based on the current user or tenant context. This works by either:
- **AST injection**: Automatically adding filter conditions to the parsed SQL.
- **Session variables**: Setting PostgreSQL session variables that trigger RLS policies.

```yaml
# config.yaml
connection_string: "postgresql://..."
schema_name: "public"
statement_timeout_ms: 10000
row_limit: 100
rls_policies:
  - column: "tenant_id"
    value: "t-12345"
table_filters:
  exclude: ["migrations", "audit_logs"]
```
```python
gq = GenQuery(llm=llm, config_path="config.yaml")
```

## Customizing the Pipeline

GenQuery's pipeline architecture makes it trivial to replace any step. For example, if you want to use your own Schema Inspector while keeping the ranker, planner, and executor running normally, you can swap out the single stage object:

```python
from genquery import GenQuery
from genquery.pipeline.inspector.inspector import SchemaInspectorStage
from genquery.pipeline.state import PipelineStage, PipelineState

# 1. Define your custom stage
class MyCustomInspector(PipelineStage):
    def run(self, state: PipelineState) -> PipelineState:
        # custom schema extraction logic here...
        state.schema_context = custom_schema_object
        return state

# 2. Instantiate genquery normally
gq = GenQuery(llm=my_llm_adapter, connection_string="...")

# 3. Replace only the target stage
gq.pipeline.replace_stage(SchemaInspectorStage, MyCustomInspector())

# 4. Run query 
result = gq.run("Find the average salary of all active employees")
```

## Callbacks and Observability

Track pipeline execution at every step using `GenQueryCallbackHandler`:

```python
from genquery.core.callbacks import GenQueryCallbackHandler

class MyLogger(GenQueryCallbackHandler):
    def on_sql_generated(self, step_id: str, sql: str) -> None:
        print(f"Generated SQL for {step_id}: {sql}")

gq = GenQuery(llm=llm, connection_string="...", callbacks=MyLogger())
```
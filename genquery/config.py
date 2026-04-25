import yaml
from pydantic import BaseModel, Field
from typing import List, Optional, Pattern
import os

class TableFilterConfig(BaseModel):
    include: Optional[List[str]] = None
    exclude: Optional[List[str]] = None
    regex: Optional[Pattern | str] = None
    prefix: Optional[str] = None
    suffix: Optional[str] = None

class RLSPolicy(BaseModel):
    column: str
    value: str
    session_variable: Optional[str] = None

class PromptsConfig(BaseModel):
    """
    Configuration for prompt paths. Defaults will be loaded if empty or file not found.
    """
    ranker_prompt_path: Optional[str] = None
    planner_prompt_path: Optional[str] = None
    generator_prompt_path: Optional[str] = None
    def load_prompt(self, path_attr: str, default_prompt: str) -> str:
        """
        Helper to load a prompt from file if specified, else returning the default.
        """
        prompt_path = getattr(self, path_attr)
        if prompt_path and os.path.exists(prompt_path):
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        return default_prompt

class GenQueryConfig(BaseModel):
    connection_string: str
    schema_name: str = "public"
    table_filters: TableFilterConfig = Field(default_factory=TableFilterConfig)
    prompts: PromptsConfig = Field(default_factory=PromptsConfig)
    rls_policies: List[RLSPolicy] = Field(default_factory=list)
    statement_timeout_ms: int = 15000
    schema_cache_ttl_seconds: int = 3600
    schema_cache_dir: str = ".gq_cache"
    row_limit: int = 1000

    @classmethod
    def from_yaml(cls, path: str, connection_string: Optional[str] = None, schema_name: Optional[str] = None) -> "GenQueryConfig":
        if not os.path.exists(path):
            raise FileNotFoundError(f"Config file not found at: {path}")
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        if not data:
            data = {}
        if connection_string:
            data['connection_string'] = connection_string
        elif 'connection_string' not in data or not data['connection_string']:
            raise ValueError("connection_string must be provided if config_path is not specified")
        if schema_name:
            data['schema_name'] = schema_name
        return cls(**data)

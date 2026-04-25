import yaml
from pydantic import BaseModel, Field
from typing import List, Optional, Pattern, Any
import os

class TableFilterConfig(BaseModel):
    include: Optional[List[str]] = None
    exclude: Optional[List[str]] = None
    regex: Optional[Pattern | str] = None
    prefix: Optional[str] = None
    suffix: Optional[str] = None

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

    @classmethod
    def from_yaml(cls, path: str) -> "GenQueryConfig":
        if not os.path.exists(path):
            raise FileNotFoundError(f"Config file not found at: {path}")
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        if not data:
            data = {}
        return cls(**data)

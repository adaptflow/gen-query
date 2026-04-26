import os
import json
import time
import hashlib
from typing import Optional
from genquery.core.models import SchemaContext
from genquery.config import GenQueryConfig

class SchemaCache:
    def __init__(self, config: GenQueryConfig):
        self.config = config
        self.cache_dir = config.schema_cache_dir
        self.ttl = config.schema_cache_ttl_seconds
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir, exist_ok=True)
            
    def _get_cache_key(self) -> str:
        # Create a deterministic key based on connection and schema config
        base_str = f"{self.config.connection_string}_{self.config.schema_name}"
        hash_str = hashlib.md5(base_str.encode()).hexdigest()
        return f"schema_cache_{hash_str}.json"
        
    def _get_cache_path(self) -> str:
        return os.path.join(self.cache_dir, self._get_cache_key())

    def get(self) -> Optional[SchemaContext]:
        if self.ttl <= 0:
            return None
            
        path = self._get_cache_path()
        if not os.path.exists(path):
            return None
            
        # Check TTL
        mtime = os.path.getmtime(path)
        if (time.time() - mtime) > self.ttl:
            return None
            
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return SchemaContext(**data)
        except Exception:
            return None
            
    def set(self, schema_context: SchemaContext):
        if self.ttl <= 0:
            return
            
        path = self._get_cache_path()
        try:
            with open(path, 'w', encoding='utf-8') as f:
                # Pydantic v2 dump
                json.dump(schema_context.model_dump(), f)
        except Exception as e:
            print(f"Warning: Failed to save schema cache - {e}")

    def should_refresh_soon(self, threshold: float = 0.8) -> bool:
        """Returns True if the cache is past `threshold`% of its TTL."""
        if self.ttl <= 0:
            return False
            
        path = self._get_cache_path()
        if not os.path.exists(path):
            return True
            
        mtime = os.path.getmtime(path)
        age = time.time() - mtime
        return age > (self.ttl * threshold)

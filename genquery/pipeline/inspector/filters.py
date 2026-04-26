import re
from genquery.config import TableFilterConfig

def should_include_table(table_name: str, config: TableFilterConfig) -> bool:
    """
    Determine if a table should be included in the schema context based on filter configuration.
    """
    if config.exclude and table_name in config.exclude:
        return False
    
    if config.include and table_name not in config.include:
        return False
        
    if config.prefix and not table_name.startswith(config.prefix):
        return False
        
    if config.suffix and not table_name.endswith(config.suffix):
        return False
        
    if config.regex:
        pattern = re.compile(config.regex) if isinstance(config.regex, str) else config.regex
        if not pattern.match(table_name):
            return False
            
    return True

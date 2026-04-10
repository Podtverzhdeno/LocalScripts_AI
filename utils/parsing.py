"""
Robust JSON parsing utilities for LLM outputs.

Handles common issues with 7B-11B models:
- Trailing commas
- Unquoted keys
- Markdown code blocks
- Incomplete JSON
- Comments in JSON
"""

import json
import re
from typing import TypeVar, Type, Optional, Any, Dict
from langchain_core.language_models import BaseChatModel

try:
    from pydantic import BaseModel, ValidationError
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    BaseModel = object
    ValidationError = Exception


T = TypeVar('T')


def parse_json_robust(
    response: str,
    schema: Optional[Type[T]] = None,
    llm: Optional[BaseChatModel] = None,
    fallback_to_minimal: bool = True
) -> Any:
    """
    Robust JSON parsing with multiple fallback strategies.

    Args:
        response: LLM response (potentially invalid JSON)
        schema: Pydantic model for validation (optional)
        llm: LLM for JSON repair (optional, last resort)
        fallback_to_minimal: Return minimal valid structure on failure

    Returns:
        Parsed and validated data (dict or Pydantic model)

    Raises:
        ValueError: If all parsing strategies fail and fallback_to_minimal=False
    """

    # Strategy 1: Direct parse
    result = _try_direct_parse(response, schema)
    if result is not None:
        return result

    # Strategy 2: Extract from markdown code blocks
    result = _try_markdown_extract(response, schema)
    if result is not None:
        return result

    # Strategy 3: Find JSON object with regex
    result = _try_regex_extract(response, schema)
    if result is not None:
        return result

    # Strategy 4: Fix common JSON issues
    result = _try_fix_common_issues(response, schema)
    if result is not None:
        return result

    # Strategy 5: Use LLM to repair JSON (if available)
    if llm:
        result = _try_llm_repair(response, schema, llm)
        if result is not None:
            return result

    # Strategy 6: Return minimal valid structure
    if fallback_to_minimal and schema and PYDANTIC_AVAILABLE:
        print(f"[WARNING] All JSON parsing strategies failed. Returning minimal structure.")
        return _create_minimal_from_schema(schema)

    raise ValueError(f"Failed to parse JSON after all strategies. Response: {response[:200]}")


def _try_direct_parse(response: str, schema: Optional[Type[T]]) -> Optional[Any]:
    """Try direct JSON parsing."""
    try:
        data = json.loads(response)
        if schema and PYDANTIC_AVAILABLE and issubclass(schema, BaseModel):
            return schema(**data)
        return data
    except (json.JSONDecodeError, ValidationError, TypeError):
        return None


def _try_markdown_extract(response: str, schema: Optional[Type[T]]) -> Optional[Any]:
    """Extract JSON from markdown code blocks."""
    json_match = re.search(
        r'```(?:json)?\s*(\{.*?\})\s*```',
        response,
        re.DOTALL
    )
    if json_match:
        try:
            data = json.loads(json_match.group(1))
            if schema and PYDANTIC_AVAILABLE and issubclass(schema, BaseModel):
                return schema(**data)
            return data
        except (json.JSONDecodeError, ValidationError, TypeError):
            pass
    return None


def _try_regex_extract(response: str, schema: Optional[Type[T]]) -> Optional[Any]:
    """Find JSON object with regex (greedy match)."""
    json_match = re.search(
        r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',
        response,
        re.DOTALL
    )
    if json_match:
        try:
            data = json.loads(json_match.group(0))
            if schema and PYDANTIC_AVAILABLE and issubclass(schema, BaseModel):
                return schema(**data)
            return data
        except (json.JSONDecodeError, ValidationError, TypeError):
            pass
    return None


def _try_fix_common_issues(response: str, schema: Optional[Type[T]]) -> Optional[Any]:
    """Fix common JSON issues and try parsing."""
    cleaned = response.strip()

    # Remove trailing commas before closing brackets
    cleaned = re.sub(r',(\s*[}\]])', r'\1', cleaned)

    # Remove comments (not valid JSON)
    cleaned = re.sub(r'//.*?\n', '\n', cleaned)
    cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL)

    # Try to fix unquoted keys (risky, only for simple word keys)
    # Only apply if it looks like unquoted keys are the issue
    if re.search(r'{\s*\w+\s*:', cleaned):
        cleaned_with_quotes = re.sub(r'(\w+):', r'"\1":', cleaned)
        try:
            data = json.loads(cleaned_with_quotes)
            if schema and PYDANTIC_AVAILABLE and issubclass(schema, BaseModel):
                return schema(**data)
            return data
        except (json.JSONDecodeError, ValidationError, TypeError):
            pass

    # Try without the unquoted key fix
    try:
        data = json.loads(cleaned)
        if schema and PYDANTIC_AVAILABLE and issubclass(schema, BaseModel):
            return schema(**data)
        return data
    except (json.JSONDecodeError, ValidationError, TypeError):
        pass

    return None


def _try_llm_repair(
    response: str,
    schema: Optional[Type[T]],
    llm: BaseChatModel
) -> Optional[Any]:
    """Use LLM to repair invalid JSON."""
    try:
        schema_info = ""
        if schema and PYDANTIC_AVAILABLE and issubclass(schema, BaseModel):
            schema_info = f"\n\nExpected schema:\n{schema.schema_json(indent=2)}"

        repair_prompt = f"""Fix this invalid JSON. Return ONLY valid JSON, no explanations.

Invalid JSON:
{response[:1000]}
{schema_info}

Valid JSON:"""

        repaired = llm.invoke(repair_prompt)
        if hasattr(repaired, 'content'):
            repaired = repaired.content

        data = json.loads(repaired)
        if schema and PYDANTIC_AVAILABLE and issubclass(schema, BaseModel):
            return schema(**data)
        return data
    except (json.JSONDecodeError, ValidationError, TypeError, Exception):
        return None


def _create_minimal_from_schema(schema: Type[T]) -> T:
    """Create minimal valid instance from Pydantic schema."""
    if not PYDANTIC_AVAILABLE or not issubclass(schema, BaseModel):
        return {}

    fields = schema.__fields__
    minimal_data = {}

    for field_name, field_info in fields.items():
        field_type = field_info.annotation

        # Handle common types
        if field_type == str or field_type == Optional[str]:
            minimal_data[field_name] = ""
        elif field_type == int or field_type == Optional[int]:
            minimal_data[field_name] = 0
        elif field_type == float or field_type == Optional[float]:
            minimal_data[field_name] = 0.0
        elif field_type == bool or field_type == Optional[bool]:
            minimal_data[field_name] = False
        elif str(field_type).startswith('list') or str(field_type).startswith('typing.List'):
            minimal_data[field_name] = []
        elif str(field_type).startswith('dict') or str(field_type).startswith('typing.Dict'):
            minimal_data[field_name] = {}
        else:
            # For complex types, try to instantiate or use None
            try:
                if hasattr(field_type, '__call__'):
                    minimal_data[field_name] = field_type()
                else:
                    minimal_data[field_name] = None
            except:
                minimal_data[field_name] = None

    return schema(**minimal_data)


def parse_text_list(text: str, separator: str = '|') -> list[list[str]]:
    """
    Parse simple text list format.

    Example:
        config.lua | Configuration settings | none
        db.lua | Database operations | config.lua

    Returns:
        [['config.lua', 'Configuration settings', 'none'],
         ['db.lua', 'Database operations', 'config.lua']]
    """
    lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
    result = []

    for line in lines:
        # Skip comments or empty lines
        if line.startswith('#') or line.startswith('//'):
            continue

        parts = [part.strip() for part in line.split(separator)]
        if parts:
            result.append(parts)

    return result


def parse_function_signatures(text: str) -> list[dict[str, str]]:
    """
    Parse function signature format.

    Example:
        connect(url) -> connection
        query(conn, sql) -> results

    Returns:
        [{'name': 'connect', 'params': 'url', 'returns': 'connection'},
         {'name': 'query', 'params': 'conn, sql', 'returns': 'results'}]
    """
    lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
    result = []

    for line in lines:
        # Skip comments
        if line.startswith('#') or line.startswith('//') or line.startswith('--'):
            continue

        # Match: function_name(params) -> return_type
        match = re.match(r'(\w+)\((.*?)\)\s*->\s*(.+)', line)
        if match:
            result.append({
                'name': match.group(1),
                'params': match.group(2).strip(),
                'returns': match.group(3).strip()
            })

    return result


def parse_structured_text(text: str, section_separator: str = '---') -> list[dict[str, str]]:
    """
    Parse structured text format with sections.

    Example:
        FILE: auth.lua
        PROBLEM: calls db.connect() but function not found
        FIX: db.lua should export connect() function
        ---
        FILE: api.lua
        PROBLEM: missing error handling
        FIX: wrap calls in pcall()

    Returns:
        [{'FILE': 'auth.lua', 'PROBLEM': '...', 'FIX': '...'},
         {'FILE': 'api.lua', 'PROBLEM': '...', 'FIX': '...'}]
    """
    sections = text.strip().split(section_separator)
    result = []

    for section in sections:
        section = section.strip()
        if not section:
            continue

        item = {}
        for line in section.split('\n'):
            line = line.strip()
            if not line:
                continue

            # Match: KEY: value
            match = re.match(r'([A-Z_]+):\s*(.+)', line)
            if match:
                item[match.group(1)] = match.group(2).strip()

        if item:
            result.append(item)

    return result

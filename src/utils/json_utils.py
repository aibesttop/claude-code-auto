import json
import re
from typing import Any, Optional, Union, List, Dict

def extract_json(text: str) -> Optional[Union[Dict, List]]:
    """
    Robustly extracts the first valid JSON object or array from text.
    Handles markdown code blocks, XML-like tags, and surrounding text.
    """
    # 1. Try to find JSON within markdown code blocks
    code_block_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
    matches = re.findall(code_block_pattern, text)
    for match in matches:
        try:
            return json.loads(match)
        except json.JSONDecodeError:
            continue

    # 2. Try to find JSON-like structures (objects or arrays)
    # This regex looks for the outermost {} or []
    # It's a simple approximation and might need a parser for nested structures if regex fails,
    # but for LLM output it's often sufficient to find the first '{' and last '}'
    
    # Find the first '{' or '['
    start_idx = -1
    stack = []
    
    for i, char in enumerate(text):
        if char in '{[':
            if not stack:
                start_idx = i
            stack.append(char)
        elif char in '}]':
            if not stack:
                continue
            
            last = stack[-1]
            if (char == '}' and last == '{') or (char == ']' and last == '['):
                stack.pop()
                if not stack:
                    # Found a complete block
                    json_str = text[start_idx : i + 1]
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        # Keep searching if this one failed
                        continue
            else:
                # Mismatched brackets, reset
                stack = []
                start_idx = -1

    # 3. Fallback: Try to clean up common issues like </arg_value>
    cleaned_text = text.replace("</arg_value>", "").strip()
    try:
        return json.loads(cleaned_text)
    except json.JSONDecodeError:
        pass

    return None

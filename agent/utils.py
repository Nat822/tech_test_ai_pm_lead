"""
Utility helpers — JSON extraction from LLM responses.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Type, TypeVar

from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


# ---------------------------------------------------------------------------
# JSON extraction
# ---------------------------------------------------------------------------

def extract_json(text: str) -> dict:
    """
    Extract the first JSON object from an LLM response.
    Tries multiple strategies in order of reliability:
      1. ```json ... ``` code-fenced blocks
      2. ``` ... ``` code-fenced blocks
      3. Outermost { } pair found by bracket scanning (handles nesting)
      4. Regex greedy fallback
    """
    if not text or not text.strip():
        raise ValueError("LLM returned an empty response.")

    # 1. Try markdown code fence with json tag
    fence_match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence_match:
        try:
            return json.loads(fence_match.group(1))
        except json.JSONDecodeError:
            pass

    # 2. Try any markdown code fence
    fence_match = re.search(r"```\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence_match:
        try:
            return json.loads(fence_match.group(1))
        except json.JSONDecodeError:
            pass

    # 3. Scan for outermost { } pair (bracket counting — handles nested objects)
    start = text.find("{")
    if start != -1:
        depth = 0
        in_string = False
        escape_next = False
        for i, ch in enumerate(text[start:], start=start):
            if escape_next:
                escape_next = False
                continue
            if ch == "\\" and in_string:
                escape_next = True
                continue
            if ch == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[start: i + 1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        break  # malformed — fall through to next strategy

    # 4. Greedy regex fallback
    brace_match = re.search(r"\{.*\}", text, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError(
        f"No JSON object found in LLM response. "
        f"Preview: {text[:400]!r}"
    )


def parse_llm_response(text: str, model_class: Type[T]) -> T:
    """
    Parse and validate an LLM text response into a Pydantic model.
    Raises ValueError with a descriptive message on failure.
    """
    # Log the raw response so failures are debuggable in server console
    logger.info("LLM raw response (first 800 chars): %.800s", text)
    try:
        data = extract_json(text)
        return model_class.model_validate(data)
    except (json.JSONDecodeError, ValueError) as exc:
        logger.error("JSON parse error: %s | Full response: %.800s", exc, text)
        raise ValueError(f"LLM returned invalid JSON: {exc}") from exc

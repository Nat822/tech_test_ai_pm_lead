"""
NeuralDeep LLM client — chat completions + embeddings.

Uses the OpenAI-compatible API via the `openai` SDK.
All I/O is wrapped in asyncio.to_thread so FastAPI async routes
are never blocked by the sync SDK calls.
"""
from __future__ import annotations

import asyncio
import logging
import os

from dotenv import load_dotenv
from openai import OpenAI, APIError, RateLimitError, APITimeoutError

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Singleton client — created once at import time
# ---------------------------------------------------------------------------
_client = OpenAI(
    api_key=os.getenv("NEURALDEEP_API_KEY"),
    base_url=os.getenv("NEURALDEEP_BASE_URL", "https://api.neuraldeep.ru/v1"),
)

MODEL: str = os.getenv("NEURALDEEP_MODEL", "GPT-OSS-120B")
EMBED_MODEL: str = os.getenv("NEURALDEEP_EMBED_MODEL", "bge-m3")


# ---------------------------------------------------------------------------
# Chat completions
# ---------------------------------------------------------------------------

async def nd_chat(
    messages: list[dict],
    temperature: float = 0.2,
    max_tokens: int = 2000,
) -> str:
    """
    Send a chat completion request to NeuralDeep.

    Runs the sync SDK call in a thread-pool so the FastAPI event loop
    is never blocked.
    """

    def _call() -> str:
        response = _client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=90,  # seconds — must be < Streamlit read_timeout (120s)
        )
        choice = response.choices[0]
        content = choice.message.content
        if content is None:
            raise ValueError(
                f"Model returned empty content. finish_reason={choice.finish_reason}"
            )
        if choice.finish_reason == "length":
            logger.warning(
                "LLM response was TRUNCATED by token limit (max_tokens=%d). "
                "JSON will likely be invalid. Consider increasing max_tokens.",
                max_tokens,
            )
        return content

    try:
        result = await asyncio.to_thread(_call)
        if result is None:
            raise ValueError("LLM returned None content. The model may have refused the request or hit a content filter.")
        return result
    except RateLimitError as exc:
        logger.error("NeuralDeep rate limit: %s", exc)
        raise
    except APITimeoutError as exc:
        logger.error("NeuralDeep timeout: %s", exc)
        raise
    except APIError as exc:
        logger.error("NeuralDeep API error: %s", exc)
        raise


# ---------------------------------------------------------------------------
# Embeddings
# ---------------------------------------------------------------------------

async def nd_embed(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for a list of texts via NeuralDeep.
    """

    def _call() -> list[list[float]]:
        response = _client.embeddings.create(
            model=EMBED_MODEL,
            input=texts,
        )
        return [e.embedding for e in response.data]

    try:
        return await asyncio.to_thread(_call)
    except APIError as exc:
        logger.error("NeuralDeep embeddings error: %s", exc)
        raise

"""
POST /requirements_diff — analyse requirement changes using RAG + LLM.
"""
from __future__ import annotations

import json
import logging

from fastapi import APIRouter, HTTPException

from agent.llm import nd_chat
from agent.models.requirements import RequirementsDiff, RequirementsDiffRequest
from agent.rag import retrieve
from agent.utils import parse_llm_response

logger = logging.getLogger(__name__)

router = APIRouter(tags=["requirements"])

_SCHEMA = json.dumps(RequirementsDiff.model_json_schema(), ensure_ascii=False)

SYSTEM_PROMPT = f"""\
Ты — экспертный ИИ-бизнес-аналитик. Твоя задача — проанализировать ЖУРНАЛ ИЗМЕНЕНИЙ требований проекта.

ВАЖНО: Анализируй ТОЛЬКО раздел «Журнал изменений требований» (или аналогичный).
НЕ перечисляй содержимое всего документа. Ищи конкретные изменения между версиями (v1.0→v1.1, v1.1→v1.2 и т.д.).

Правила ответа:
- Отвечай ТОЛЬКО валидным JSON-объектом без какого-либо текста до или после него
- ВСЕ строковые значения на РУССКОМ языке (переводи даже если источник на английском)
- Каждый список — максимум 3 пункта, каждый пункт — до 8 слов
- Не добавляй пояснений, предисловий, markdown-разметки

Что помещать в каждое поле:
- "added": требования, которые были ДОБАВЛЕНЫ в новых версиях
- "changed": требования, которые были ИЗМЕНЕНЫ (формат: «было X, стало Y»)
- "removed": требования, которые были УДАЛЕНЫ из документа
- "conflicts": противоречия между участниками по требованиям
- "current_hypothesis": 1-2 предложения об актуальном состоянии требований

Точная JSON-схема ответа:
{_SCHEMA}
"""


@router.post(
    "/requirements_diff",
    response_model=RequirementsDiff,
    summary="Analyse requirement changes",
)
async def requirements_diff(req: RequirementsDiffRequest) -> RequirementsDiff:
    """
    Retrieve requirement-related context and produce a structured diff
    of added, changed, removed requirements and conflicts.
    """
    query = (
        f"журнал изменений требований добавлено удалено изменено противоречия проект {req.project} "
        f"{req.extra_context}"
    ).strip()

    try:
        context = await retrieve(query)
    except Exception as exc:
        logger.error("RAG retrieval failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"RAG error: {exc}") from exc

    user_content = (
        f"Проект: {req.project}\n"
        f"Дополнительный контекст: {req.extra_context}\n\n"
        f"=== ИЗВЛЕЧЁННЫЕ ФРАГМЕНТЫ ДОКУМЕНТАЦИИ ===\n{context}\n\n"
        f"Задача: найди в тексте выше ТОЛЬКО изменения требований между версиями и заполни JSON. "
        f"Каждый пункт — краткая формулировка на русском языке (1 предложение). "
        f"Максимум 5 пунктов в каждом списке."
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]

    try:
        raw = await nd_chat(messages, max_tokens=1200)
    except Exception as exc:
        logger.error("LLM call failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"LLM error: {exc}") from exc

    try:
        return parse_llm_response(raw, RequirementsDiff)
    except ValueError as exc:
        logger.error("Response parse error: %s | Raw: %.600s", exc, raw)
        raise HTTPException(status_code=422, detail=str(exc)) from exc

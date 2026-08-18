"""
POST /prepare_meeting — prepare a structured meeting brief using RAG + LLM.
"""
from __future__ import annotations

import json
import logging

from fastapi import APIRouter, HTTPException

from agent.llm import nd_chat
from agent.models.meeting import MeetingPrep, MeetingPrepRequest
from agent.rag import retrieve
from agent.utils import parse_llm_response

logger = logging.getLogger(__name__)

router = APIRouter(tags=["meeting"])

_SCHEMA = json.dumps(MeetingPrep.model_json_schema(), ensure_ascii=False)

SYSTEM_PROMPT = f"""\
Ты — экспертный ИИ-помощник для руководителя проектов. Подготовь краткий брифинг к встрече.

Правила ответа:
- Отвечай ТОЛЬКО валидным JSON-объектом без какого-либо текста до или после него
- ВСЕ строковые значения на РУССКОМ языке (переводи даже если источник на английском)
- Каждый список — максимум 3 пункта, каждый пункт — до 8 слов
- Не добавляй пояснений, предисловий, markdown-разметки

Что помещать в каждое поле:
- "context": 2 предложения о текущем состоянии проекта
- "decisions": уже принятые ключевые решения
- "open_questions": нерешённые вопросы, требующие обсуждения
- "must_ask": самые критичные вопросы для предстоящей встречи
- "unfulfilled_promises": взятые, но ещё не выполненные обязательства

Точная JSON-схема ответа:
{_SCHEMA}
"""


@router.post("/prepare_meeting", response_model=MeetingPrep, summary="Prepare meeting brief")
async def prepare_meeting(req: MeetingPrepRequest) -> MeetingPrep:
    """
    Retrieve relevant context for the project and generate a structured
    meeting preparation brief using the LLM.
    """
    query = (
        f"встреча решения открытые вопросы обязательства блокеры проект {req.project} "
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
        f"Задача: на основе текста выше заполни JSON для брифинга к встрече. "
        f"Каждый пункт — краткая формулировка на русском (1 предложение). "
        f"Максимум 4 пункта в каждом списке."
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
        return parse_llm_response(raw, MeetingPrep)
    except ValueError as exc:
        logger.error("Response parse error: %s | Raw: %.600s", exc, raw)
        raise HTTPException(status_code=422, detail=str(exc)) from exc

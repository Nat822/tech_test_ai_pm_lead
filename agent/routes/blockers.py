"""
POST /find_blockers — identify technical and organizational blockers using RAG + LLM.
"""
from __future__ import annotations

import json
import logging

from fastapi import APIRouter, HTTPException

from agent.llm import nd_chat
from agent.models.blockers import Blockers, BlockersRequest
from agent.rag import retrieve
from agent.utils import parse_llm_response

logger = logging.getLogger(__name__)

router = APIRouter(tags=["blockers"])

_SCHEMA = json.dumps(Blockers.model_json_schema(), ensure_ascii=False)

SYSTEM_PROMPT = f"""\
Ты — экспертный ИИ-менеджер проектов и аналитик рисков. Найди блокеры проекта.

Правила ответа:
- Отвечай ТОЛЬКО валидным JSON-объектом без какого-либо текста до или после него
- ВСЕ строковые значения на РУССКОМ языке
- Максимум 2 пункта в каждом списке, каждый пункт — не более 8 слов
- Не добавляй пояснений, предисловий, markdown-разметки

Что помещать в каждое поле:
- "technical": технические препятствия (оборудование, зависимости, производительность)
- "organizational": организационные препятствия (бюджет, кадры, юридические вопросы)
- "responsibles": простые строки формата «Имя ответственного: действие для устранения блокера»
- "next_steps": конкретные действия для устранения блокеров

Точная JSON-схема ответа:
{_SCHEMA}
"""


@router.post("/find_blockers", response_model=Blockers, summary="Identify project blockers")
async def find_blockers(req: BlockersRequest) -> Blockers:
    """
    Retrieve blocker-related context and generate a structured list of
    technical and organizational blockers with responsible owners.
    """
    query = (
        f"блокеры риски проблемы задержки препятствия проект {req.project} "
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
        f"Задача: найди ТОЛЬКО блокеры из текста выше, заполни JSON. "
        f"Поле 'responsibles' — строки вида 'Имя: действие'. "
        f"Максимум 2 пункта в каждом списке. Каждый пункт — до 8 слов. Всё на русском."
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
        return parse_llm_response(raw, Blockers)
    except ValueError as exc:
        logger.error("Response parse error: %s | Raw: %.600s", exc, raw)
        raise HTTPException(status_code=422, detail=str(exc)) from exc

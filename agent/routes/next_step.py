"""
POST /next_step_task — generate and persist a next-action task using RAG + LLM.
"""
from __future__ import annotations

import json
import logging

from fastapi import APIRouter, HTTPException

from agent.llm import nd_chat
from agent.models.task import NextStepRequest, TaskModel
from agent.rag import retrieve
from agent.tasks import save_task
from agent.utils import parse_llm_response

logger = logging.getLogger(__name__)

router = APIRouter(tags=["next_step"])

_SCHEMA = json.dumps(TaskModel.model_json_schema(), ensure_ascii=False)

SYSTEM_PROMPT = f"""\
Ты — экспертный ИИ-менеджер проектов. Определи ОДНО наиболее критичное следующее действие.

Правила ответа:
- Отвечай ТОЛЬКО валидным JSON-объектом без какого-либо текста до или после него
- ВСЕ строковые значения на РУССКОМ языке (переводи даже если источник на английском)
- Будь лаконичен: title — до 80 символов, description — 2-3 предложения
- Не добавляй пояснений, предисловий, markdown-разметки

Что помещать в каждое поле:
- "title": краткое действие-глагол (например: «Получить одобрение бюджета у CFO»)
- "description": почему это самое важное сейчас и что конкретно нужно сделать
- "priority": "high", "medium" или "low"
- "assignee": имя ответственного из документа (если есть)

Точная JSON-схема ответа:
{_SCHEMA}
"""


@router.post("/next_step_task", response_model=TaskModel, summary="Generate and create next task")
async def next_step_task(req: NextStepRequest) -> TaskModel:
    """
    Generate the most critical next action for the project using RAG context,
    persist it to tasks.json, and return the created task.
    """
    query = (
        f"следующие шаги приоритеты критические действия блокеры проект {req.project} "
        f"{req.situation}"
    ).strip()

    try:
        context = await retrieve(query)
    except Exception as exc:
        logger.error("RAG retrieval failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"RAG error: {exc}") from exc

    user_content = (
        f"Проект: {req.project}\n"
        f"Текущая ситуация: {req.situation}\n\n"
        f"=== ИЗВЛЕЧЁННЫЕ ФРАГМЕНТЫ ДОКУМЕНТАЦИИ ===\n{context}\n\n"
        f"Задача: определи ОДНО наиболее критичное действие прямо сейчас. "
        f"Заполни JSON кратко на русском языке."
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]

    try:
        raw = await nd_chat(messages, max_tokens=400)
    except Exception as exc:
        logger.error("LLM call failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"LLM error: {exc}") from exc

    try:
        task = parse_llm_response(raw, TaskModel)
    except ValueError as exc:
        logger.error("Response parse error: %s | Raw: %.600s", exc, raw)
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    # Persist to tasks.json
    try:
        save_task(task)
    except OSError as exc:
        logger.error("Failed to save task: %s", exc)
        raise HTTPException(status_code=500, detail=f"Task save error: {exc}") from exc

    return task

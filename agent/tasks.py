"""
Tasks API — storage and router for project tasks.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException

from agent.models.task import TaskModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["tasks"])

TASKS_FILE = Path(__file__).parent / "tasks.json"


# ---------------------------------------------------------------------------
# Storage helpers
# ---------------------------------------------------------------------------

def save_task(task: TaskModel) -> None:
    """Append a task as a JSON line to tasks.json."""
    with open(TASKS_FILE, "a", encoding="utf-8") as fh:
        fh.write(task.model_dump_json() + "\n")
    logger.info("Task saved: %s", task.title)


def load_tasks() -> list[dict]:
    """Read all tasks from tasks.json (NDJSON format)."""
    if not TASKS_FILE.exists():
        return []
    tasks: list[dict] = []
    with open(TASKS_FILE, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    tasks.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    logger.warning("Skipping malformed task line: %s", exc)
    return tasks


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/", summary="Create a new task")
async def create_task(task: TaskModel) -> dict:
    """Persist a task to tasks.json and return it."""
    try:
        save_task(task)
    except OSError as exc:
        logger.error("Failed to write task: %s", exc)
        raise HTTPException(status_code=500, detail=f"Could not save task: {exc}") from exc
    return {"status": "ok", "task": task.model_dump()}


@router.get("/", summary="List all tasks")
async def list_tasks() -> dict:
    """Return all persisted tasks."""
    return {"tasks": load_tasks()}

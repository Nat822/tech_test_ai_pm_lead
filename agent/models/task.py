from typing import Literal

from pydantic import BaseModel


class TaskModel(BaseModel):
    title: str
    description: str
    priority: Literal["high", "medium", "low"] = "medium"
    assignee: str


class NextStepRequest(BaseModel):
    project: str
    situation: str = ""

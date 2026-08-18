from pydantic import BaseModel


class BlockersRequest(BaseModel):
    project: str
    extra_context: str = ""


class Blockers(BaseModel):
    technical: list[str]
    organizational: list[str]
    responsibles: list[str]   # формат: "Имя: действие для устранения блокера"
    next_steps: list[str]

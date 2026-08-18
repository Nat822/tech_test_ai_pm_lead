from pydantic import BaseModel


class RequirementsDiffRequest(BaseModel):
    project: str
    extra_context: str = ""


class ConflictItem(BaseModel):
    description: str
    parties: list[str]
    status: str  # "pending" | "resolved"


class RequirementsDiff(BaseModel):
    added: list[str]
    changed: list[str]
    removed: list[str]
    conflicts: list[ConflictItem]
    current_hypothesis: str

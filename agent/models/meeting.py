from pydantic import BaseModel


class MeetingPrepRequest(BaseModel):
    project: str
    extra_context: str = ""


class MeetingPrep(BaseModel):
    context: str
    decisions: list[str]
    open_questions: list[str]
    must_ask: list[str]
    unfulfilled_promises: list[str]

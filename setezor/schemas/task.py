from typing import Optional
from pydantic import BaseModel
from pydantic.networks import IPv4Address, IPv4Network



class TaskStatus:
    started = "STARTED"
    finished = "FINISHED"
    failed = "FAILED"
    created = "CREATED"
    pre_canceled = "PRE_CANCELED"
    canceled = "CANCELED"
    registered = "REGISTERED"
    stopped = "STOPPED"


class TaskPayload(BaseModel):
    task_id: str
    project_id: Optional[str]
    agent_id: str
    job_params: dict
    job_name: str


class WebSocketMessage(BaseModel):
    title: str
    text: str
    type: str
    command: str = "notify"
    user_id: str | None = None


class TaskPayloadWithScopeID(BaseModel):
    scope_id: str | None = None

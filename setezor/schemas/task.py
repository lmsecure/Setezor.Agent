from typing import Optional
from pydantic import BaseModel
from pydantic.networks import IPv4Address, IPv4Network



class TaskStatus:
    created = "CREATED"
    registered = "REGISTERED"
    processing_on_agent = "PROCESSING_ON_AGENT"
    finished_on_agent = "FINISHED_ON_AGENT"
    processing_on_server = "PROCESSING_ON_SERVER"
    pre_canceled = "PRE_CANCELED"
    canceled = "CANCELED"
    soft_stopped = "SOFTSTOPPED"
    finished = "FINISHED"
    failed = "FAILED"


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

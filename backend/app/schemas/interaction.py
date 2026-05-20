import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.interaction import InteractionStatus, InteractionType


#request schema

class InteractionCreate(BaseModel):
    hcp_id: uuid.UUID
    rep_id: str = Field(..., max_length=100)
    interaction_type: InteractionType
    occurred_at: datetime
    location: str | None = None
    duration_minutes: int | None = Field(None, ge=1, le=480)
    raw_notes: str | None = None
    products_discussed: list[str] | None = None
    next_steps: str | None = None


class InteractionUpdate(BaseModel):
    """All fields optional — supports partial PATCH semantics."""
    interaction_type: InteractionType | None = None
    occurred_at: datetime | None = None
    location: str | None = None
    duration_minutes: int | None = None
    raw_notes: str | None = None
    products_discussed: list[str] | None = None
    next_steps: str | None = None
    status: InteractionStatus | None = None


class ChatMessage(BaseModel):
   
    hcp_id: uuid.UUID
    rep_id: str
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: str | None = None  # for multi-turn continuity


#responnse schema

class FollowUpOut(BaseModel):
    id: uuid.UUID
    due_date: str
    task_description: str
    status: str

    model_config = {"from_attributes": True}


class InteractionOut(BaseModel):
    id: uuid.UUID
    hcp_id: uuid.UUID
    rep_id: str
    interaction_type: InteractionType
    occurred_at: datetime
    location: str | None
    duration_minutes: int | None
    raw_notes: str | None
    ai_summary: str | None
    products_discussed: list[str] | None
    sentiment: str | None
    key_topics: list[str] | None
    next_steps: str | None
    status: InteractionStatus
    follow_ups: list[FollowUpOut]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AgentResponse(BaseModel):
    
    reply: str
    interaction: InteractionOut | None = None
    action_taken: str | None = None  # e.g. "log_interaction", "schedule_followup"
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AssignmentCreate(BaseModel):
    incident_id: str
    responder_id: str


class AssignmentUpdate(BaseModel):
    status: str = Field(pattern="^(ASSIGNED|IN_PROGRESS|RESOLVED)$")
    resolution_note: str | None = None


class AssignmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    incident_id: str
    responder_id: str
    assigned_by: str
    status: str
    resolution_note: str | None
    created_at: datetime
    updated_at: datetime

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditEventCreate(BaseModel):
    action: str
    resource_type: str
    resource_id: str | None = None
    details: str | None = None


class AuditEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    actor_id: str | None
    action: str
    resource_type: str
    resource_id: str | None
    details: str | None
    created_at: datetime

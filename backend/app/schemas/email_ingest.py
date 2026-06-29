from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class EmailIngestSettings(BaseModel):
    enabled: bool
    address: Optional[str] = None
    instructions: str


class EmailIngestLogResponse(BaseModel):
    id: int
    sender: Optional[str] = None
    subject: Optional[str] = None
    items_created: int
    attachments_processed: int
    errors: Optional[list[str]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class EmailIngestResult(BaseModel):
    items_created: int = 0
    attachments_processed: int = 0
    errors: list[str] = Field(default_factory=list)
    log_id: Optional[int] = None

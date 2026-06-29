from typing import Optional

from pydantic import BaseModel, Field


class PushTokenRegister(BaseModel):
    token: str = Field(min_length=10)
    platform: Optional[str] = None
    timezone: str = "UTC"


class PushTokenUnregister(BaseModel):
    token: str = Field(min_length=10)


class NotificationTestResult(BaseModel):
    title: str
    body: str
    tokens_sent: int
    push_result: dict

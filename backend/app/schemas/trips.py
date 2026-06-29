from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TripPlanCreate(BaseModel):
    destination: str = Field(min_length=1, max_length=120)
    weather_tag: Optional[str] = Field(default=None, max_length=30)
    days: int = Field(default=1, ge=1, le=60)
    notes: Optional[str] = Field(default=None, max_length=500)


class TripPlanUpdate(BaseModel):
    destination: Optional[str] = Field(default=None, min_length=1, max_length=120)
    weather_tag: Optional[str] = Field(default=None, max_length=30)
    days: Optional[int] = Field(default=None, ge=1, le=60)
    notes: Optional[str] = Field(default=None, max_length=500)
    is_completed: Optional[bool] = None


class TripPlanResponse(TripPlanCreate):
    id: int
    user_id: int
    is_completed: bool
    created_at: datetime

    class Config:
        from_attributes = True


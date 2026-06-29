from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.closet import ClothingItemResponse


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


class TripDayOutfit(BaseModel):
    day: int
    title: str
    rationale: Optional[str] = None
    top: Optional[ClothingItemResponse] = None
    bottom: Optional[ClothingItemResponse] = None
    shoes: Optional[ClothingItemResponse] = None
    outerwear: Optional[ClothingItemResponse] = None


class TripPackingPlan(BaseModel):
    trip: TripPlanResponse
    days: List[TripDayOutfit]
    packing_list: List[ClothingItemResponse]
    summary: str


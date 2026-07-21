from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field, model_validator

from app.schemas.closet import ClothingItemResponse


class TripPlanCreate(BaseModel):
    destination: str = Field(min_length=1, max_length=120)
    weather_tag: Optional[str] = Field(default=None, max_length=30)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    days: int = Field(default=1, ge=1, le=60)
    notes: Optional[str] = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def normalize_trip_dates(self) -> "TripPlanCreate":
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValueError("end_date must be on or after start_date")
            self.days = (self.end_date - self.start_date).days + 1
        return self


class TripPlanUpdate(BaseModel):
    destination: Optional[str] = Field(default=None, min_length=1, max_length=120)
    weather_tag: Optional[str] = Field(default=None, max_length=30)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
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
    trip_date: Optional[date] = None
    weather_tag: Optional[str] = None
    weather_summary: Optional[str] = None
    rationale: Optional[str] = None
    top: Optional[ClothingItemResponse] = None
    bottom: Optional[ClothingItemResponse] = None
    shoes: Optional[ClothingItemResponse] = None
    outerwear: Optional[ClothingItemResponse] = None
    dress: Optional[ClothingItemResponse] = None


class TripPackingPlan(BaseModel):
    trip: TripPlanResponse
    days: List[TripDayOutfit]
    packing_list: List[ClothingItemResponse]
    summary: str
    weather_source: Optional[str] = None
    weather_note: Optional[str] = None


class TripDayLock(BaseModel):
    day: int = Field(ge=1)
    top_id: Optional[int] = None
    bottom_id: Optional[int] = None
    shoes_id: Optional[int] = None
    outerwear_id: Optional[int] = None


class TripPackingReshuffleRequest(BaseModel):
    day: int = Field(ge=1)
    locked_days: List[TripDayLock] = Field(default_factory=list)

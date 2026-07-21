from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.closet import ClothingItemResponse


class OutfitSuggestionRequest(BaseModel):
    occasion: Optional[str] = None
    weather_tag: Optional[str] = None
    include_alternative: bool = True


class OutfitSuggestion(BaseModel):
    title: str
    weather_tag: Optional[str] = None
    occasion: Optional[str] = None
    trend: Optional[str] = None
    rationale: Optional[str] = None
    styling_note: Optional[str] = None
    top: Optional[ClothingItemResponse] = None
    bottom: Optional[ClothingItemResponse] = None
    shoes: Optional[ClothingItemResponse] = None
    outerwear: Optional[ClothingItemResponse] = None
    dress: Optional[ClothingItemResponse] = None
    bag: Optional[ClothingItemResponse] = None
    accessory: Optional[ClothingItemResponse] = None
    headwear: Optional[ClothingItemResponse] = None
    alternatives: List[ClothingItemResponse] = []


class OutfitDirection(OutfitSuggestion):
    """One of the three Phase 7 styling directions (classic/expressive/relaxed)."""

    direction: str
    label: str
    tagline: str


class OutfitDirectionsResponse(BaseModel):
    weather_tag: Optional[str] = None
    occasion: Optional[str] = None
    directions: List[OutfitDirection] = []


class PlanActivity(BaseModel):
    activity: str
    occasion: str
    mode: str  # "wear" (now) or "pack" (bring along)
    title: str
    rationale: Optional[str] = None
    top: Optional[ClothingItemResponse] = None
    bottom: Optional[ClothingItemResponse] = None
    shoes: Optional[ClothingItemResponse] = None
    outerwear: Optional[ClothingItemResponse] = None
    dress: Optional[ClothingItemResponse] = None
    packing_list: List[ClothingItemResponse] = []


class DailyPlan(BaseModel):
    weather_tag: Optional[str] = None
    activities: List[PlanActivity] = []
    routine_enabled: Optional[bool] = None
    source: Optional[str] = None


class DailyRoutineResponse(BaseModel):
    enabled: bool = True
    wake_time: str = "07:00"
    weekday_activities: List[str] = []
    weekend_activities: List[str] = []
    gym_days: List[str] = []
    default_weather_tag: Optional[str] = None
    notifications_enabled: bool = False
    timezone: str = "UTC"


class DailyRoutineUpdate(BaseModel):
    enabled: Optional[bool] = None
    wake_time: Optional[str] = None
    weekday_activities: Optional[List[str]] = None
    weekend_activities: Optional[List[str]] = None
    gym_days: Optional[List[str]] = None
    default_weather_tag: Optional[str] = None
    notifications_enabled: Optional[bool] = None
    timezone: Optional[str] = None


class OutfitFeedbackCreate(BaseModel):
    top_id: Optional[int] = None
    bottom_id: Optional[int] = None
    shoes_id: Optional[int] = None
    outerwear_id: Optional[int] = None
    dress_id: Optional[int] = None
    signal: str  # like | dislike | wore
    occasion: Optional[str] = None
    weather_tag: Optional[str] = None


class OutfitFeedbackResponse(BaseModel):
    id: int
    signal: int
    created_at: datetime

    class Config:
        from_attributes = True


class TrendOption(BaseModel):
    id: str
    label: str


class ParsedOutfitIntent(BaseModel):
    occasion: Optional[str] = None
    weather_tag: Optional[str] = None
    trend: Optional[str] = None
    formality: Optional[str] = None
    direction: Optional[str] = None
    preferred_colors: list[str] = []
    excluded_tokens: list[str] = []
    anchor_item_id: Optional[int] = None
    anchor_label: Optional[str] = None
    exclude_item_ids: list[int] = []
    freshness_slot: Optional[str] = None
    interpretation: str


class OutfitAskRequest(BaseModel):
    query: str = Field(min_length=3, max_length=500)


class OutfitAskResponse(BaseModel):
    query: str
    parsed: ParsedOutfitIntent
    suggestion: OutfitSuggestion


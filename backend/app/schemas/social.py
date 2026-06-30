from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.closet import ClothingItemResponse


class SocialPostCreate(BaseModel):
    caption: Optional[str] = Field(default=None, max_length=400)
    top_id: Optional[int] = None
    bottom_id: Optional[int] = None
    shoes_id: Optional[int] = None
    outerwear_id: Optional[int] = None


class SocialPostResponse(BaseModel):
    id: int
    user_id: int
    user_name: str
    caption: Optional[str] = None
    look_name: Optional[str] = None
    occasion: Optional[str] = None
    photo_url: Optional[str] = None
    top: Optional[ClothingItemResponse] = None
    bottom: Optional[ClothingItemResponse] = None
    shoes: Optional[ClothingItemResponse] = None
    outerwear: Optional[ClothingItemResponse] = None
    reactions_count: int
    comments_count: int
    liked_by_me: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class SocialPostLikeResponse(BaseModel):
    liked: bool
    reactions_count: int


class StreakResponse(BaseModel):
    current_streak: int
    longest_streak: int
    total_fit_days: int
    active_this_week: int
    last_active_date: Optional[date] = None
    timezone: str

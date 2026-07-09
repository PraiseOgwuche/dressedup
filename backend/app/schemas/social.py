from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.schemas.closet import ClothingItemResponse

FeedScope = Literal["all", "following", "mine"]


class SocialPostCreate(BaseModel):
    caption: Optional[str] = Field(default=None, max_length=400)
    look_name: Optional[str] = Field(default=None, max_length=120)
    occasion: Optional[str] = Field(default=None, max_length=50)
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
    is_mine: bool = False
    following_author: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class SocialPostLikeResponse(BaseModel):
    liked: bool
    reactions_count: int


class SocialCommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=400)


class SocialCommentResponse(BaseModel):
    id: int
    post_id: int
    user_id: int
    user_name: str
    body: str
    is_mine: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class SocialUserSummary(BaseModel):
    id: int
    full_name: str
    post_count: int
    follower_count: int
    is_following: bool = False
    is_self: bool = False


class SocialFollowResponse(BaseModel):
    following: bool
    follower_count: int


class StreakResponse(BaseModel):
    current_streak: int
    longest_streak: int
    total_fit_days: int
    active_this_week: int
    last_active_date: Optional[date] = None
    timezone: str


FeedActivityType = Literal["like", "comment", "follow", "new_post", "streak_nudge"]


class FeedActivityItem(BaseModel):
    id: str
    type: FeedActivityType
    actor_user_id: Optional[int] = None
    actor_name: str
    message: str
    post_id: Optional[int] = None
    created_at: datetime
    is_unread: bool = False


class FeedActivityResponse(BaseModel):
    items: list[FeedActivityItem]
    unread_count: int
    last_seen_at: Optional[datetime] = None


class FeedActivitySeenResponse(BaseModel):
    last_seen_at: datetime
    unread_count: int = 0

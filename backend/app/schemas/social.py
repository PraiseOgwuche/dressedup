from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SocialPostCreate(BaseModel):
    caption: str = Field(min_length=1, max_length=400)
    look_name: Optional[str] = Field(default=None, max_length=120)
    occasion: Optional[str] = Field(default=None, max_length=50)


class SocialPostResponse(SocialPostCreate):
    id: int
    user_id: int
    reactions_count: int
    comments_count: int
    created_at: datetime

    class Config:
        from_attributes = True


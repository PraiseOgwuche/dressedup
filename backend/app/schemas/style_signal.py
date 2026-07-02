from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

StyleEventType = Literal[
    "like",
    "dislike",
    "wore",
    "swap",
    "shop_tap",
    "shop_preview",
    "feed_share",
    "feed_like",
]


class StyleSignalCreate(BaseModel):
    event_type: StyleEventType
    top_id: Optional[int] = None
    bottom_id: Optional[int] = None
    shoes_id: Optional[int] = None
    outerwear_id: Optional[int] = None
    swap_slot: Optional[str] = None
    replaced_item_id: Optional[int] = None
    product_id: Optional[str] = Field(default=None, max_length=64)
    post_id: Optional[int] = None
    occasion: Optional[str] = None
    weather_tag: Optional[str] = None


class StyleSignalResponse(BaseModel):
    id: int
    event_type: str
    created_at: datetime

    class Config:
        from_attributes = True

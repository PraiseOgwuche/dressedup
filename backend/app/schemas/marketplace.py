from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.schemas.closet import ClothingItemResponse

ListingType = Literal["sell", "gift"]
ListingCondition = Literal["like_new", "good", "fair"]
ListingStatus = Literal["active", "gone", "removed"]


class ClosetListingCreate(BaseModel):
    clothing_item_id: int
    listing_type: ListingType
    title: Optional[str] = Field(default=None, max_length=120)
    description: Optional[str] = Field(default=None, max_length=600)
    price_cents: Optional[int] = Field(default=None, ge=0)
    condition: ListingCondition = "good"


class ClosetListingUpdate(BaseModel):
    description: Optional[str] = Field(default=None, max_length=600)
    price_cents: Optional[int] = Field(default=None, ge=0)
    condition: Optional[ListingCondition] = None
    status: Optional[ListingStatus] = None


class ClosetListingResponse(BaseModel):
    id: int
    user_id: int
    seller_name: str
    listing_type: ListingType
    title: str
    description: Optional[str] = None
    price_cents: Optional[int] = None
    condition: ListingCondition
    status: ListingStatus
    is_mine: bool = False
    item: ClothingItemResponse
    created_at: datetime

    class Config:
        from_attributes = True


class ListingInterestResponse(BaseModel):
    mailto: str
    seller_name: str

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ClothingItemBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    category: str = Field(min_length=2, max_length=50)
    subcategory: Optional[str] = Field(default=None, max_length=50)
    brand: Optional[str] = Field(default=None, max_length=80)
    product_name: Optional[str] = Field(default=None, max_length=120)
    size: Optional[str] = Field(default=None, max_length=30)
    color: Optional[str] = Field(default=None, max_length=50)
    color_hex: Optional[str] = Field(default=None, max_length=9)
    pattern: Optional[str] = Field(default=None, max_length=40)
    material: Optional[str] = Field(default=None, max_length=120)
    occasion: Optional[list[str]] = None
    formality: Optional[str] = Field(default=None, max_length=40)
    weather_tag: Optional[list[str]] = None
    seasons: Optional[list[str]] = None
    image_url: Optional[str] = Field(default=None, max_length=500)
    thumbnail_url: Optional[str] = Field(default=None, max_length=500)
    is_clean: bool = True


class ClothingItemCreate(ClothingItemBase):
    # Provenance from AI ingestion; manual adds default to "manual".
    source: str = Field(default="manual", max_length=20)
    confidence: Optional[dict[str, float]] = None
    needs_review: bool = False
    ai_metadata: Optional[dict] = None


class ClothingItemUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    category: Optional[str] = Field(default=None, min_length=2, max_length=50)
    subcategory: Optional[str] = Field(default=None, max_length=50)
    brand: Optional[str] = Field(default=None, max_length=80)
    product_name: Optional[str] = Field(default=None, max_length=120)
    size: Optional[str] = Field(default=None, max_length=30)
    color: Optional[str] = Field(default=None, max_length=50)
    color_hex: Optional[str] = Field(default=None, max_length=9)
    pattern: Optional[str] = Field(default=None, max_length=40)
    material: Optional[str] = Field(default=None, max_length=120)
    occasion: Optional[list[str]] = None
    formality: Optional[str] = Field(default=None, max_length=40)
    weather_tag: Optional[list[str]] = None
    seasons: Optional[list[str]] = None
    image_url: Optional[str] = Field(default=None, max_length=500)
    thumbnail_url: Optional[str] = Field(default=None, max_length=500)
    is_clean: Optional[bool] = None
    times_worn: Optional[int] = Field(default=None, ge=0)
    needs_review: Optional[bool] = None


class ClothingItemResponse(ClothingItemBase):
    id: int
    user_id: int
    times_worn: int
    wears_since_wash: int
    last_worn_at: Optional[datetime] = None
    last_washed_at: Optional[datetime] = None
    wear_limit: Optional[int] = None
    effective_wear_limit: Optional[int] = None
    source: str
    needs_review: bool
    created_at: datetime

    class Config:
        from_attributes = True


class WashAllRequest(BaseModel):
    # Specific dirty items to wash; omit/empty to wash everything in the hamper.
    item_ids: Optional[list[int]] = None


class LaundrySummary(BaseModel):
    clean_count: int
    dirty_count: int
    laundry_due: bool
    depleted_categories: list[str]
    clean_by_category: dict[str, int]
    dirty_by_category: dict[str, int]
    message: str

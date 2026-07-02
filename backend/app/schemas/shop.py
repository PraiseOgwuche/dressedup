from typing import List, Optional

from pydantic import BaseModel, Field


class ShopOutfitGarment(BaseModel):
    id: int
    name: str
    category: str
    color: Optional[str] = None
    image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    is_shop_pick: bool = False


class ShopOutfitPreview(BaseModel):
    score: float = Field(..., ge=0, le=1)
    top: Optional[ShopOutfitGarment] = None
    bottom: Optional[ShopOutfitGarment] = None
    shoes: Optional[ShopOutfitGarment] = None
    outerwear: Optional[ShopOutfitGarment] = None


class ShopRecommendation(BaseModel):
    product_id: str
    brand: str
    name: str
    category: str
    color: Optional[str] = None
    price_usd: float
    product_url: str
    buy_url: str
    image_url: Optional[str] = None
    retailer: Optional[str] = None
    pitch: str
    outfit_count: int = Field(..., ge=0)
    sample_outfits: List[ShopOutfitPreview] = Field(default_factory=list)
    reason: str
    priority: str


class ShopRecommendationResponse(BaseModel):
    summary: str
    styling_insight: Optional[str] = None
    recommendations: List[ShopRecommendation]

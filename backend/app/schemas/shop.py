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


class ShopGapCard(BaseModel):
    title: str
    category: str
    closet_count: int = Field(..., ge=0)
    reason: str
    unlock_outfits: int = Field(0, ge=0)
    product_id: Optional[str] = None
    product_brand: Optional[str] = None
    product_name: Optional[str] = None
    image_url: Optional[str] = None
    price_usd: Optional[float] = None


class ShopRecommendationResponse(BaseModel):
    summary: str
    styling_insight: Optional[str] = None
    gap_card: Optional[ShopGapCard] = None
    recommendations: List[ShopRecommendation]

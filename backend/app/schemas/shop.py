from typing import List, Optional

from pydantic import BaseModel, Field


class ShopRecommendation(BaseModel):
    product_id: str
    brand: str
    name: str
    category: str
    color: Optional[str] = None
    price_usd: float
    product_url: str
    pitch: str
    outfit_count: int = Field(..., ge=0)
    reason: str
    priority: str


class ShopRecommendationResponse(BaseModel):
    summary: str
    recommendations: List[ShopRecommendation]

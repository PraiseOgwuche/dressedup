from typing import List

from pydantic import BaseModel


class ShopRecommendation(BaseModel):
    category: str
    reason: str
    priority: str


class ShopRecommendationResponse(BaseModel):
    recommendations: List[ShopRecommendation]


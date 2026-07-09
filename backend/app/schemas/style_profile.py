from typing import List, Optional

from pydantic import BaseModel, Field


class StyleProfileStat(BaseModel):
    label: str
    value: int = Field(..., ge=0)


class StyleProfileActivity(BaseModel):
    wore: int = 0
    likes: int = 0
    swaps: int = 0
    shop_explores: int = 0
    feed_shares: int = 0


class StyleProfileResponse(BaseModel):
    headline: str
    summary: str
    top_colors: List[StyleProfileStat] = Field(default_factory=list)
    top_categories: List[StyleProfileStat] = Field(default_factory=list)
    formality_zone: Optional[str] = None
    top_occasions: List[str] = Field(default_factory=list)
    activity: StyleProfileActivity
    insights: List[str] = Field(default_factory=list)
    signal_count: int = 0

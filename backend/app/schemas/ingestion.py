from typing import Optional

from pydantic import BaseModel, Field


class DraftItem(BaseModel):
    """AI-proposed clothing item the user confirms or corrects before saving.

    The stable contract every VisionProvider returns. `confidence` maps field
    name -> 0.0-1.0; low-confidence fields drive what the UI asks the user about.
    """

    name: str
    category: str
    subcategory: Optional[str] = None
    brand: Optional[str] = None
    product_name: Optional[str] = None
    size: Optional[str] = None
    color: Optional[str] = None
    color_hex: Optional[str] = None
    pattern: Optional[str] = None
    material: Optional[str] = None
    occasion: list[str] = Field(default_factory=list)
    formality: Optional[str] = None
    weather_tag: list[str] = Field(default_factory=list)
    seasons: list[str] = Field(default_factory=list)

    source: str = "photo"
    confidence: dict[str, float] = Field(default_factory=dict)
    needs_review: bool = False


class IngestResult(BaseModel):
    """Returned by the ingest endpoint: the AI draft plus the stored image URLs.
    The client lets the user confirm/edit, then saves via POST /closet/items."""

    draft: DraftItem
    image_url: str
    thumbnail_url: str


class BatchIngestEntry(BaseModel):
    """One image's outcome in a bulk scan. Either `result` or `error` is set, so a
    single bad photo never fails the whole batch."""

    filename: Optional[str] = None
    result: Optional[IngestResult] = None
    error: Optional[str] = None


class BatchIngestResult(BaseModel):
    entries: list[BatchIngestEntry]


class MultiIngestEntry(BaseModel):
    index: int
    draft: DraftItem
    image_url: str
    thumbnail_url: str


class MultiIngestResult(BaseModel):
    """One photo segmented into several confirmable drafts (flat-lay / outfit pile)."""

    source_image_url: str
    entries: list[MultiIngestEntry]

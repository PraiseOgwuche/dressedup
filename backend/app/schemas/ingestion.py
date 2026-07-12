from typing import Optional

from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    """Normalized garment box in the source photo (fractions of width/height)."""

    x: float = Field(ge=0.0, le=1.0)
    y: float = Field(ge=0.0, le=1.0)
    w: float = Field(gt=0.0, le=1.0)
    h: float = Field(gt=0.0, le=1.0)


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

    # Flat-lay localization — used to crop a per-item photo before cutout.
    bbox: Optional[BoundingBox] = None

    # Receipt / purchase metadata (Phase F). Persisted in ClothingItem.ai_metadata on save.
    sku: Optional[str] = None
    price: Optional[float] = Field(default=None, description="Unit price in USD when known.")
    purchase_date: Optional[str] = Field(default=None, description="ISO date from receipt when known.")


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


class CutoutBackfillResult(BaseModel):
    updated: int
    skipped: int
    updated_ids: list[int] = Field(default_factory=list)


class ReceiptIngestResult(BaseModel):
    """Retail receipt photo → merchant context plus one draft per clothing line item."""

    source_image_url: str
    merchant: Optional[str] = None
    purchase_date: Optional[str] = None
    entries: list[MultiIngestEntry]


class ReceiptExtract(BaseModel):
    """Raw vision output for a receipt (before storage URLs are attached)."""

    merchant: Optional[str] = None
    purchase_date: Optional[str] = None
    items: list[DraftItem]

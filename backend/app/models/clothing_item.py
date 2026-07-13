from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ClothingItem(Base):
    __tablename__ = "clothing_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Identity
    name = Column(String, nullable=False)
    brand = Column(String, nullable=True)
    product_name = Column(String, nullable=True)
    size = Column(String, nullable=True)

    # Classification
    category = Column(String, nullable=False, index=True)
    subcategory = Column(String, nullable=True, index=True)

    # Visual attributes
    color = Column(String, nullable=True)
    color_hex = Column(String, nullable=True)
    pattern = Column(String, nullable=True)
    material = Column(String, nullable=True)

    # Context. occasion + weather_tag are lists ("all that apply"); seasons too.
    occasion = Column(JSON, nullable=True)
    formality = Column(String, nullable=True)
    weather_tag = Column(JSON, nullable=True)
    seasons = Column(JSON, nullable=True)
    # Soft capsules / groupings (travel, work, date…) — not outfit-matching taxonomy.
    tags = Column(JSON, nullable=True)

    # Media
    image_url = Column(String, nullable=True)
    thumbnail_url = Column(String, nullable=True)

    # State / wear tracking
    is_clean = Column(Boolean, default=True)
    times_worn = Column(Integer, default=0)  # lifetime wears
    wears_since_wash = Column(Integer, nullable=False, server_default="0", default=0)
    last_worn_at = Column(DateTime(timezone=True), nullable=True)
    last_washed_at = Column(DateTime(timezone=True), nullable=True)
    # Per-item override of the category wear limit; NULL uses the category default.
    wear_limit = Column(Integer, nullable=True)

    # Provenance / AI ingestion
    source = Column(String, nullable=False, server_default="manual", default="manual")
    confidence = Column(JSON, nullable=True)  # {field: 0.0-1.0}
    needs_review = Column(Boolean, default=False)
    ai_metadata = Column(JSON, nullable=True)  # raw extractor output for audit

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="closet_items")

    @property
    def effective_wear_limit(self) -> int | None:
        """Wears-before-wash in effect: per-item override, else category default.
        None means this item is not laundered by wear (e.g. jewelry)."""
        from app.taxonomy import wear_limit_for

        return self.wear_limit if self.wear_limit is not None else wear_limit_for(self.category)

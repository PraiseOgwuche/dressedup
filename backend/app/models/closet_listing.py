from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ClosetListing(Base):
    """Peer listing to sell or gift a closet item — no in-app messaging in v1."""

    __tablename__ = "closet_listings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    clothing_item_id = Column(
        Integer, ForeignKey("clothing_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    listing_type = Column(String(16), nullable=False)  # sell | gift
    title = Column(String(120), nullable=False)
    description = Column(Text, nullable=True)
    price_cents = Column(Integer, nullable=True)
    condition = Column(String(32), nullable=False, default="good")
    status = Column(String(16), nullable=False, default="active", index=True)  # active | gone | removed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User")
    item = relationship("ClothingItem")

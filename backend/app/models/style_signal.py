from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class StyleSignal(Base):
    """Unified activity log for personalization — wears, swaps, shop taps, feed shares."""

    __tablename__ = "style_signals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    event_type = Column(String(32), nullable=False, index=True)
    top_id = Column(Integer, ForeignKey("clothing_items.id"), nullable=True)
    bottom_id = Column(Integer, ForeignKey("clothing_items.id"), nullable=True)
    shoes_id = Column(Integer, ForeignKey("clothing_items.id"), nullable=True)
    outerwear_id = Column(Integer, ForeignKey("clothing_items.id"), nullable=True)
    dress_id = Column(Integer, ForeignKey("clothing_items.id"), nullable=True)
    swap_slot = Column(String(16), nullable=True)
    replaced_item_id = Column(Integer, ForeignKey("clothing_items.id"), nullable=True)
    product_id = Column(String(64), nullable=True)
    post_id = Column(Integer, ForeignKey("social_posts.id"), nullable=True)
    occasion = Column(String, nullable=True)
    weather_tag = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="style_signals")

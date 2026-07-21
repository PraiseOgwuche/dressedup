from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base

# Explicit feedback signals stored as integers for simple aggregation.
SIGNAL_WORE = 2
SIGNAL_LIKE = 3
SIGNAL_DISLIKE = -3


class OutfitFeedback(Base):
    __tablename__ = "outfit_feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    top_id = Column(Integer, ForeignKey("clothing_items.id"), nullable=True)
    bottom_id = Column(Integer, ForeignKey("clothing_items.id"), nullable=True)
    shoes_id = Column(Integer, ForeignKey("clothing_items.id"), nullable=True)
    outerwear_id = Column(Integer, ForeignKey("clothing_items.id"), nullable=True)
    dress_id = Column(Integer, ForeignKey("clothing_items.id"), nullable=True)
    signal = Column(Integer, nullable=False)
    occasion = Column(String, nullable=True)
    weather_tag = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="outfit_feedback")

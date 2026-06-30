from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class SocialPost(Base):
    __tablename__ = "social_posts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    caption = Column(Text, nullable=True)
    look_name = Column(String, nullable=True)
    occasion = Column(String, nullable=True)
    top_id = Column(Integer, ForeignKey("clothing_items.id"), nullable=True)
    bottom_id = Column(Integer, ForeignKey("clothing_items.id"), nullable=True)
    shoes_id = Column(Integer, ForeignKey("clothing_items.id"), nullable=True)
    outerwear_id = Column(Integer, ForeignKey("clothing_items.id"), nullable=True)
    photo_url = Column(String(500), nullable=True)
    reactions_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="social_posts")
    likes = relationship("SocialPostLike", back_populates="post", cascade="all, delete-orphan")
    top = relationship("ClothingItem", foreign_keys=[top_id])
    bottom = relationship("ClothingItem", foreign_keys=[bottom_id])
    shoes = relationship("ClothingItem", foreign_keys=[shoes_id])
    outerwear = relationship("ClothingItem", foreign_keys=[outerwear_id])

from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class SocialPostLike(Base):
    __tablename__ = "social_post_likes"
    __table_args__ = (UniqueConstraint("post_id", "user_id", name="uq_social_post_likes_post_user"),)

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("social_posts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    post = relationship("SocialPost", back_populates="likes")
    user = relationship("User")

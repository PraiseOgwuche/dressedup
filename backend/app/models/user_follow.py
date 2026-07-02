from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class UserFollow(Base):
    __tablename__ = "user_follows"
    __table_args__ = (UniqueConstraint("follower_id", "following_id", name="uq_user_follows_pair"),)

    id = Column(Integer, primary_key=True, index=True)
    follower_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    following_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    follower = relationship("User", foreign_keys=[follower_id], back_populates="following_links")
    following = relationship("User", foreign_keys=[following_id], back_populates="follower_links")

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import secrets

from app.database import Base


def _new_ingest_token() -> str:
    return secrets.token_hex(8)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_premium = Column(Boolean, default=False)
    premium_trial_ends_at = Column(DateTime(timezone=True), nullable=True)
    ingest_token = Column(String(32), unique=True, index=True, nullable=False, default=_new_ingest_token)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    closet_items = relationship("ClothingItem", back_populates="user", cascade="all, delete-orphan")
    social_posts = relationship("SocialPost", back_populates="user", cascade="all, delete-orphan")
    trip_plans = relationship("TripPlan", back_populates="user", cascade="all, delete-orphan")
    daily_routine = relationship(
        "DailyRoutine", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    push_tokens = relationship("PushToken", back_populates="user", cascade="all, delete-orphan")
    email_ingest_logs = relationship(
        "EmailIngestLog", back_populates="user", cascade="all, delete-orphan"
    )
    outfit_feedback = relationship(
        "OutfitFeedback", back_populates="user", cascade="all, delete-orphan"
    )
    following_links = relationship(
        "UserFollow",
        foreign_keys="UserFollow.follower_id",
        back_populates="follower",
        cascade="all, delete-orphan",
    )
    follower_links = relationship(
        "UserFollow",
        foreign_keys="UserFollow.following_id",
        back_populates="following",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<User {self.email}>"

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class DailyRoutine(Base):
    __tablename__ = "daily_routines"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    enabled = Column(Boolean, default=True, nullable=False)
    wake_time = Column(String, nullable=False, default="07:00")
    weekday_activities = Column(JSON, nullable=False, default=list)
    weekend_activities = Column(JSON, nullable=False, default=list)
    gym_days = Column(JSON, nullable=False, default=list)
    default_weather_tag = Column(String, nullable=True)
    notifications_enabled = Column(Boolean, default=False, nullable=False)
    timezone = Column(String, nullable=False, default="UTC")
    last_morning_push_at = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="daily_routine")

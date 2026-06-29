from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class EmailIngestLog(Base):
    __tablename__ = "email_ingest_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    sender = Column(String, nullable=True)
    subject = Column(String, nullable=True)
    items_created = Column(Integer, nullable=False, default=0, server_default="0")
    attachments_processed = Column(Integer, nullable=False, default=0, server_default="0")
    errors = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="email_ingest_logs")

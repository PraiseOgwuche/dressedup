from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ListingInterest(Base):
    """Buyer expressed interest in a listing — seller sees in-app; contact stays off-app."""

    __tablename__ = "listing_interests"
    __table_args__ = (UniqueConstraint("listing_id", "user_id", name="uq_listing_interests_pair"),)

    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("closet_listings.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    listing = relationship("ClosetListing", back_populates="interests")
    user = relationship("User")

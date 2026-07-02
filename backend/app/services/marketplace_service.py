from typing import Optional
from urllib.parse import quote

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.closet_listing import ClosetListing
from app.models.clothing_item import ClothingItem
from app.models.user import User
from app.schemas.closet import ClothingItemResponse
from app.schemas.marketplace import (
    ClosetListingCreate,
    ClosetListingResponse,
    ClosetListingUpdate,
    ListingInterestResponse,
)


class MarketplaceService:
    @staticmethod
    def _serialize(listing: ClosetListing, *, viewer_id: Optional[int] = None) -> ClosetListingResponse:
        return ClosetListingResponse(
            id=listing.id,
            user_id=listing.user_id,
            seller_name=listing.user.full_name if listing.user else "Member",
            listing_type=listing.listing_type,
            title=listing.title,
            description=listing.description,
            price_cents=listing.price_cents,
            condition=listing.condition,
            status=listing.status,
            is_mine=viewer_id is not None and listing.user_id == viewer_id,
            item=ClothingItemResponse.model_validate(listing.item),
            created_at=listing.created_at,
        )

    @staticmethod
    def _base_query(db: Session):
        return db.query(ClosetListing).options(
            joinedload(ClosetListing.user),
            joinedload(ClosetListing.item),
        )

    @classmethod
    def list_browse(
        cls,
        db: Session,
        viewer_id: int,
        *,
        listing_type: Optional[str] = None,
        category: Optional[str] = None,
        query: Optional[str] = None,
        limit: int = 30,
        offset: int = 0,
    ) -> list[ClosetListingResponse]:
        limit = max(1, min(limit, 50))
        offset = max(0, offset)

        q = cls._base_query(db).filter(ClosetListing.status == "active")
        if listing_type in ("sell", "gift"):
            q = q.filter(ClosetListing.listing_type == listing_type)
        if category:
            q = q.join(ClosetListing.item).filter(ClothingItem.category == category.lower())

        if query:
            needle = query.strip().lower()
            if needle:
                q = q.filter(
                    (ClosetListing.title.ilike(f"%{needle}%"))
                    | (ClosetListing.description.ilike(f"%{needle}%"))
                )

        rows = q.order_by(ClosetListing.created_at.desc()).offset(offset).limit(limit).all()
        return [cls._serialize(row, viewer_id=viewer_id) for row in rows]

    @classmethod
    def list_mine(cls, db: Session, user_id: int) -> list[ClosetListingResponse]:
        rows = (
            cls._base_query(db)
            .filter(ClosetListing.user_id == user_id, ClosetListing.status != "removed")
            .order_by(ClosetListing.created_at.desc())
            .all()
        )
        return [cls._serialize(row, viewer_id=user_id) for row in rows]

    @classmethod
    def create_listing(cls, db: Session, user_id: int, payload: ClosetListingCreate) -> ClosetListingResponse:
        item = (
            db.query(ClothingItem)
            .filter(ClothingItem.id == payload.clothing_item_id, ClothingItem.user_id == user_id)
            .first()
        )
        if not item:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Closet item not found.")

        existing = (
            db.query(ClosetListing)
            .filter(
                ClosetListing.clothing_item_id == payload.clothing_item_id,
                ClosetListing.status == "active",
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This item is already listed.",
            )

        if payload.listing_type == "gift":
            price_cents = None
        elif payload.price_cents is None or payload.price_cents <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Price is required for sell listings.",
            )
        else:
            price_cents = payload.price_cents

        title = (payload.title or item.name).strip()
        listing = ClosetListing(
            user_id=user_id,
            clothing_item_id=item.id,
            listing_type=payload.listing_type,
            title=title,
            description=(payload.description or "").strip() or None,
            price_cents=price_cents,
            condition=payload.condition,
            status="active",
        )
        db.add(listing)
        db.commit()
        db.refresh(listing)
        listing = cls._base_query(db).filter(ClosetListing.id == listing.id).one()
        return cls._serialize(listing, viewer_id=user_id)

    @classmethod
    def update_listing(
        cls,
        db: Session,
        user_id: int,
        listing_id: int,
        payload: ClosetListingUpdate,
    ) -> ClosetListingResponse:
        listing = cls._base_query(db).filter(ClosetListing.id == listing_id).first()
        if not listing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found.")
        if listing.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your listing.")

        if payload.description is not None:
            listing.description = payload.description.strip() or None
        if payload.condition is not None:
            listing.condition = payload.condition
        if payload.price_cents is not None and listing.listing_type == "sell":
            listing.price_cents = payload.price_cents
        if payload.status is not None:
            if payload.status not in ("active", "gone", "removed"):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status.")
            listing.status = payload.status

        db.commit()
        db.refresh(listing)
        listing = cls._base_query(db).filter(ClosetListing.id == listing.id).one()
        return cls._serialize(listing, viewer_id=user_id)

    @classmethod
    def delete_listing(cls, db: Session, user_id: int, listing_id: int) -> None:
        listing = db.query(ClosetListing).filter(ClosetListing.id == listing_id).first()
        if not listing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found.")
        if listing.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your listing.")
        listing.status = "removed"
        db.commit()

    @classmethod
    def express_interest(cls, db: Session, viewer_id: int, listing_id: int) -> ListingInterestResponse:
        listing = cls._base_query(db).filter(ClosetListing.id == listing_id).first()
        if not listing or listing.status != "active":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found.")
        if listing.user_id == viewer_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This is your listing.")

        seller: User = listing.user
        buyer = db.query(User).filter(User.id == viewer_id).first()
        buyer_name = buyer.full_name if buyer else "Someone"

        price_line = "Free gift" if listing.listing_type == "gift" else f"${listing.price_cents / 100:.2f}"
        subject = quote(f"DressedUp: interested in {listing.title}")
        body = quote(
            f"Hi {seller.full_name.split()[0] if seller.full_name else 'there'},\n\n"
            f"I'm {buyer_name} and I'm interested in your DressedUp listing:\n"
            f"• {listing.title}\n"
            f"• {price_line}\n\n"
            f"Let's coordinate pickup or shipping off-app.\n"
        )
        mailto = f"mailto:{seller.email}?subject={subject}&body={body}"
        return ListingInterestResponse(mailto=mailto, seller_name=seller.full_name)

from typing import Optional
from urllib.parse import quote

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.closet_listing import ClosetListing
from app.models.clothing_item import ClothingItem
from app.models.listing_interest import ListingInterest
from app.models.user import User
from app.schemas.closet import ClothingItemResponse
from app.schemas.marketplace import (
    ClosetListingCreate,
    ClosetListingResponse,
    ClosetListingUpdate,
    ListingInterestResponse,
    MyListingInterest,
    ReceivedListingInterest,
)


class MarketplaceService:
    @staticmethod
    def _format_price_line(listing: ClosetListing) -> str:
        if listing.listing_type == "gift":
            return "Free gift"
        if listing.price_cents is None:
            return "Price TBD"
        return f"${listing.price_cents / 100:.2f}"

    @staticmethod
    def _buyer_mailto(seller: User, buyer: User, listing: ClosetListing) -> str:
        buyer_name = buyer.full_name if buyer else "Someone"
        price_line = MarketplaceService._format_price_line(listing)
        subject = quote(f"DressedUp: interested in {listing.title}")
        body = quote(
            f"Hi {seller.full_name.split()[0] if seller.full_name else 'there'},\n\n"
            f"I'm {buyer_name} and I'm interested in your DressedUp listing:\n"
            f"• {listing.title}\n"
            f"• {price_line}\n\n"
            f"Let's coordinate pickup or shipping off-app.\n"
        )
        return f"mailto:{seller.email}?subject={subject}&body={body}"

    @staticmethod
    def _seller_reply_mailto(seller: User, buyer: User, listing: ClosetListing) -> str:
        buyer_first = buyer.full_name.split()[0] if buyer.full_name else "there"
        price_line = MarketplaceService._format_price_line(listing)
        subject = quote(f"Re: {listing.title} on DressedUp")
        body = quote(
            f"Hi {buyer_first},\n\n"
            f"Thanks for your interest in my listing:\n"
            f"• {listing.title}\n"
            f"• {price_line}\n\n"
            f"Happy to coordinate pickup or shipping.\n"
        )
        return f"mailto:{buyer.email}?subject={subject}&body={body}"

    @staticmethod
    def _serialize(
        listing: ClosetListing,
        *,
        viewer_id: Optional[int] = None,
        interest_count: int = 0,
        i_am_interested: bool = False,
    ) -> ClosetListingResponse:
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
            interest_count=interest_count,
            i_am_interested=i_am_interested,
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
    def _interest_counts(cls, db: Session, listing_ids: list[int]) -> dict[int, int]:
        if not listing_ids:
            return {}
        rows = (
            db.query(ListingInterest.listing_id, func.count(ListingInterest.id))
            .filter(ListingInterest.listing_id.in_(listing_ids))
            .group_by(ListingInterest.listing_id)
            .all()
        )
        return {listing_id: int(count) for listing_id, count in rows}

    @classmethod
    def _viewer_interest_ids(cls, db: Session, viewer_id: int, listing_ids: list[int]) -> set[int]:
        if not listing_ids:
            return set()
        rows = (
            db.query(ListingInterest.listing_id)
            .filter(
                ListingInterest.user_id == viewer_id,
                ListingInterest.listing_id.in_(listing_ids),
            )
            .all()
        )
        return {row[0] for row in rows}

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
        listing_ids = [row.id for row in rows]
        interested_ids = cls._viewer_interest_ids(db, viewer_id, listing_ids)
        return [
            cls._serialize(
                row,
                viewer_id=viewer_id,
                i_am_interested=row.id in interested_ids,
            )
            for row in rows
        ]

    @classmethod
    def list_mine(cls, db: Session, user_id: int) -> list[ClosetListingResponse]:
        rows = (
            cls._base_query(db)
            .filter(ClosetListing.user_id == user_id, ClosetListing.status != "removed")
            .order_by(ClosetListing.created_at.desc())
            .all()
        )
        counts = cls._interest_counts(db, [row.id for row in rows])
        return [
            cls._serialize(row, viewer_id=user_id, interest_count=counts.get(row.id, 0))
            for row in rows
        ]

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
        counts = cls._interest_counts(db, [listing.id])
        return cls._serialize(listing, viewer_id=user_id, interest_count=counts.get(listing.id, 0))

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
    def _record_interest(cls, db: Session, viewer_id: int, listing_id: int) -> ListingInterest:
        existing = (
            db.query(ListingInterest)
            .filter(ListingInterest.listing_id == listing_id, ListingInterest.user_id == viewer_id)
            .first()
        )
        if existing:
            db.commit()
            return existing

        row = ListingInterest(listing_id=listing_id, user_id=viewer_id)
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    @classmethod
    def express_interest(cls, db: Session, viewer_id: int, listing_id: int) -> ListingInterestResponse:
        listing = cls._base_query(db).filter(ClosetListing.id == listing_id).first()
        if not listing or listing.status != "active":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found.")
        if listing.user_id == viewer_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This is your listing.")

        seller: User = listing.user
        buyer = db.query(User).filter(User.id == viewer_id).first()
        cls._record_interest(db, viewer_id, listing_id)
        mailto = cls._buyer_mailto(seller, buyer, listing)
        return ListingInterestResponse(mailto=mailto, seller_name=seller.full_name, saved=True)

    @classmethod
    def list_listing_interests(
        cls, db: Session, user_id: int, listing_id: int
    ) -> list[ReceivedListingInterest]:
        listing = cls._base_query(db).filter(ClosetListing.id == listing_id).first()
        if not listing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found.")
        if listing.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your listing.")

        rows = (
            db.query(ListingInterest)
            .options(joinedload(ListingInterest.user))
            .filter(ListingInterest.listing_id == listing_id)
            .order_by(ListingInterest.created_at.desc())
            .all()
        )
        seller = listing.user
        return [
            ReceivedListingInterest(
                id=row.id,
                listing_id=listing.id,
                listing_title=listing.title,
                listing_status=listing.status,
                buyer_user_id=row.user_id,
                buyer_name=row.user.full_name if row.user else "Member",
                created_at=row.created_at,
                mailto=cls._seller_reply_mailto(seller, row.user, listing),
            )
            for row in rows
        ]

    @classmethod
    def list_received_interests(cls, db: Session, user_id: int) -> list[ReceivedListingInterest]:
        rows = (
            db.query(ListingInterest)
            .join(ClosetListing, ClosetListing.id == ListingInterest.listing_id)
            .options(
                joinedload(ListingInterest.user),
                joinedload(ListingInterest.listing).joinedload(ClosetListing.user),
            )
            .filter(
                ClosetListing.user_id == user_id,
                ClosetListing.status != "removed",
            )
            .order_by(ListingInterest.created_at.desc())
            .limit(50)
            .all()
        )
        results: list[ReceivedListingInterest] = []
        for row in rows:
            listing = row.listing
            if not listing:
                continue
            seller = listing.user
            if not seller:
                continue
            results.append(
                ReceivedListingInterest(
                    id=row.id,
                    listing_id=listing.id,
                    listing_title=listing.title,
                    listing_status=listing.status,
                    buyer_user_id=row.user_id,
                    buyer_name=row.user.full_name if row.user else "Member",
                    created_at=row.created_at,
                    mailto=cls._seller_reply_mailto(seller, row.user, listing),
                )
            )
        return results

    @classmethod
    def list_my_interests(cls, db: Session, user_id: int) -> list[MyListingInterest]:
        rows = (
            db.query(ListingInterest)
            .options(joinedload(ListingInterest.listing).joinedload(ClosetListing.user))
            .options(joinedload(ListingInterest.listing).joinedload(ClosetListing.item))
            .filter(ListingInterest.user_id == user_id)
            .order_by(ListingInterest.created_at.desc())
            .limit(50)
            .all()
        )
        results: list[MyListingInterest] = []
        for row in rows:
            listing = row.listing
            if not listing or listing.status == "removed":
                continue
            results.append(
                MyListingInterest(
                    id=row.id,
                    listing_id=listing.id,
                    expressed_at=row.created_at,
                    listing=cls._serialize(listing, viewer_id=user_id, i_am_interested=True),
                )
            )
        return results

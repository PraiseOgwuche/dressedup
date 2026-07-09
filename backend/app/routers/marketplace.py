from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.marketplace import (
    ClosetListingCreate,
    ClosetListingResponse,
    ClosetListingUpdate,
    ListingInterestResponse,
    MyListingInterest,
    ReceivedListingInterest,
)
from app.services.marketplace_service import MarketplaceService
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/marketplace", tags=["Marketplace"])


@router.get("/listings", response_model=List[ClosetListingResponse])
def browse_listings(
    listing_type: Optional[str] = Query(default=None, description="sell or gift"),
    category: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None),
    limit: int = 30,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return MarketplaceService.list_browse(
        db,
        current_user.id,
        listing_type=listing_type,
        category=category,
        query=q,
        limit=limit,
        offset=offset,
    )


@router.get("/listings/mine", response_model=List[ClosetListingResponse])
def my_listings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return MarketplaceService.list_mine(db, current_user.id)


@router.post("/listings", response_model=ClosetListingResponse, status_code=201)
def create_listing(
    payload: ClosetListingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return MarketplaceService.create_listing(db, current_user.id, payload)


@router.patch("/listings/{listing_id}", response_model=ClosetListingResponse)
def update_listing(
    listing_id: int,
    payload: ClosetListingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return MarketplaceService.update_listing(db, current_user.id, listing_id, payload)


@router.delete("/listings/{listing_id}", status_code=204)
def delete_listing(
    listing_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    MarketplaceService.delete_listing(db, current_user.id, listing_id)


@router.post("/listings/{listing_id}/interest", response_model=ListingInterestResponse)
def express_interest(
    listing_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return MarketplaceService.express_interest(db, current_user.id, listing_id)


@router.get("/listings/{listing_id}/interests", response_model=List[ReceivedListingInterest])
def listing_interests(
    listing_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return MarketplaceService.list_listing_interests(db, current_user.id, listing_id)


@router.get("/interests/received", response_model=List[ReceivedListingInterest])
def received_interests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return MarketplaceService.list_received_interests(db, current_user.id)


@router.get("/interests/mine", response_model=List[MyListingInterest])
def my_interests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return MarketplaceService.list_my_interests(db, current_user.id)

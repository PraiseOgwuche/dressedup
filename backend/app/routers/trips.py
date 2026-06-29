from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.trips import TripPackingPlan, TripPlanCreate, TripPlanResponse, TripPlanUpdate
from app.services.trip_service import TripService
from app.utils.dependencies import require_premium_user

router = APIRouter(prefix="/trips", tags=["Trips"])


@router.get("/plans", response_model=List[TripPlanResponse])
def list_trip_plans(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_premium_user),
):
    return TripService.list_plans(db, current_user.id)


@router.post("/plans", response_model=TripPlanResponse, status_code=status.HTTP_201_CREATED)
def create_trip_plan(
    payload: TripPlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_premium_user),
):
    return TripService.create_plan(db, current_user.id, payload)


@router.put("/plans/{plan_id}", response_model=TripPlanResponse)
def update_trip_plan(
    plan_id: int,
    payload: TripPlanUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_premium_user),
):
    return TripService.update_plan(db, current_user.id, plan_id, payload)


@router.get("/plans/{plan_id}/packing", response_model=TripPackingPlan)
def get_trip_packing_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_premium_user),
):
    """One outfit per trip day plus a deduplicated packing list from the closet."""
    return TripService.packing_plan(db, current_user.id, plan_id)


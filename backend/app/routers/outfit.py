from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.outfit import DailyPlan, DailyRoutineResponse, DailyRoutineUpdate, OutfitSuggestion
from app.services.outfit_service import OutfitService
from app.services.plan_service import PlanService
from app.services.routine_service import RoutineService
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/outfits", tags=["Outfits"])


@router.get("/suggestion", response_model=OutfitSuggestion)
def get_outfit_suggestion(
    occasion: str | None = None,
    weather_tag: str | None = None,
    include_alternative: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return OutfitService.get_suggestion(
        db=db,
        user_id=current_user.id,
        weather_tag=weather_tag,
        occasion=occasion,
        include_alternative=include_alternative,
    )


@router.get("/plan", response_model=DailyPlan)
def get_daily_plan(
    activities: str = "work",
    weather_tag: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Plan the day from a comma-separated list of activities (e.g. 'work,gym').
    First activity is worn now; the rest become packing lists."""
    parsed = [a.strip() for a in activities.split(",") if a.strip()] or ["work"]
    return PlanService.daily_plan(
        db=db, user_id=current_user.id, activities=parsed, weather_tag=weather_tag
    )


@router.get("/routine", response_model=DailyRoutineResponse)
def get_daily_routine(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    routine = RoutineService.get_or_create(db, current_user.id)
    return RoutineService.to_dict(routine)


@router.put("/routine", response_model=DailyRoutineResponse)
def update_daily_routine(
    payload: DailyRoutineUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    routine = RoutineService.update(db, current_user.id, payload.model_dump(exclude_unset=True))
    return RoutineService.to_dict(routine)


@router.get("/plan/today", response_model=DailyPlan)
def get_today_plan_from_routine(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Build today's outfit plan from saved routine preferences (manual trigger)."""
    return RoutineService.today_plan(db, current_user.id)


from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.outfit import (
    DailyPlan,
    DailyRoutineResponse,
    DailyRoutineUpdate,
    OutfitFeedbackCreate,
    OutfitFeedbackResponse,
    OutfitSuggestion,
    TrendOption,
)
from app.services.outfit_service import OutfitService
from app.services.plan_service import PlanService
from app.services.preference_service import PreferenceService
from app.services.routine_service import RoutineService
from app.fashion.trend_rules import available_trends
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/outfits", tags=["Outfits"])


@router.get("/suggestion", response_model=OutfitSuggestion)
def get_outfit_suggestion(
    occasion: str | None = None,
    weather_tag: str | None = None,
    trend: str | None = None,
    include_alternative: bool = True,
    swap_slot: str | None = None,
    top_id: int | None = None,
    bottom_id: int | None = None,
    shoes_id: int | None = None,
    outerwear_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Swap one piece: pass current outfit ids + swap_slot (top|bottom|shoes|outerwear)."""
    if swap_slot is not None and swap_slot not in {"top", "bottom", "shoes", "outerwear"}:
        raise HTTPException(
            status_code=400,
            detail="swap_slot must be top, bottom, shoes, or outerwear",
        )
    try:
        return OutfitService.get_suggestion(
            db=db,
            user_id=current_user.id,
            weather_tag=weather_tag,
            occasion=occasion,
            include_alternative=include_alternative,
            swap_slot=swap_slot,
            top_id=top_id,
            bottom_id=bottom_id,
            shoes_id=shoes_id,
            outerwear_id=outerwear_id,
            trend=trend,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/trends", response_model=list[TrendOption])
def list_outfit_trends():
    """Aesthetic vibes from the fashion rulebook (quiet-luxury, streetwear, etc.)."""
    return available_trends()


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


@router.post("/feedback", response_model=OutfitFeedbackResponse, status_code=201)
def record_outfit_feedback(
    payload: OutfitFeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Record like / dislike / wore — powers personalization layer."""
    if payload.signal not in {"like", "dislike", "wore"}:
        raise HTTPException(status_code=400, detail="signal must be like, dislike, or wore")
    return PreferenceService.record(
        db,
        current_user.id,
        top_id=payload.top_id,
        bottom_id=payload.bottom_id,
        shoes_id=payload.shoes_id,
        outerwear_id=payload.outerwear_id,
        signal=payload.signal,
        occasion=payload.occasion,
        weather_tag=payload.weather_tag,
    )


"""User daily routine preferences and today's plan from saved settings."""

from datetime import date
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.daily_routine import DailyRoutine
from app.services.plan_service import PlanService

_WEEKDAY_CODES = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")

_DEFAULT_WEEKDAY = ["work"]
_DEFAULT_WEEKEND = ["everyday"]


class RoutineService:
    @staticmethod
    def get_or_create(db: Session, user_id: int) -> DailyRoutine:
        routine = db.query(DailyRoutine).filter(DailyRoutine.user_id == user_id).first()
        if routine:
            return routine
        routine = DailyRoutine(
            user_id=user_id,
            weekday_activities=list(_DEFAULT_WEEKDAY),
            weekend_activities=list(_DEFAULT_WEEKEND),
            gym_days=[],
        )
        db.add(routine)
        db.commit()
        db.refresh(routine)
        return routine

    @staticmethod
    def update(db: Session, user_id: int, payload: dict) -> DailyRoutine:
        routine = RoutineService.get_or_create(db, user_id)
        for key, value in payload.items():
            if value is not None and hasattr(routine, key):
                setattr(routine, key, value)
        db.commit()
        db.refresh(routine)
        return routine

    @staticmethod
    def activities_for_today(routine: DailyRoutine, today: Optional[date] = None) -> List[str]:
        today = today or date.today()
        code = _WEEKDAY_CODES[today.weekday()]
        is_weekend = code in ("sat", "sun")
        base = list(routine.weekend_activities if is_weekend else routine.weekday_activities)
        if not base:
            base = list(_DEFAULT_WEEKEND if is_weekend else _DEFAULT_WEEKDAY)
        gym_days = [d.lower() for d in (routine.gym_days or [])]
        if "gym" not in base and code in gym_days:
            base.append("gym")
        return base

    @staticmethod
    def today_plan(db: Session, user_id: int, today: Optional[date] = None) -> dict:
        routine = RoutineService.get_or_create(db, user_id)
        activities = RoutineService.activities_for_today(routine, today=today)
        plan = PlanService.daily_plan(
            db=db,
            user_id=user_id,
            activities=activities,
            weather_tag=routine.default_weather_tag,
        )
        plan["routine_enabled"] = routine.enabled
        plan["source"] = "routine"
        return plan

    @staticmethod
    def to_dict(routine: DailyRoutine) -> dict:
        return {
            "enabled": routine.enabled,
            "wake_time": routine.wake_time,
            "weekday_activities": routine.weekday_activities or [],
            "weekend_activities": routine.weekend_activities or [],
            "gym_days": routine.gym_days or [],
            "default_weather_tag": routine.default_weather_tag,
            "notifications_enabled": routine.notifications_enabled,
            "timezone": routine.timezone or "UTC",
        }

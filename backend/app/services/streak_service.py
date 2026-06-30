from datetime import UTC, date, datetime, timedelta
from typing import Iterable
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.models.daily_routine import DailyRoutine
from app.models.outfit_feedback import SIGNAL_WORE, OutfitFeedback
from app.models.social_post import SocialPost
from app.schemas.social import StreakResponse


def _resolve_timezone(db: Session, user_id: int, timezone: str | None) -> str:
    if timezone:
        try:
            ZoneInfo(timezone)
            return timezone
        except Exception:
            pass
    routine = db.query(DailyRoutine).filter(DailyRoutine.user_id == user_id).first()
    if routine and routine.timezone:
        try:
            ZoneInfo(routine.timezone)
            return routine.timezone
        except Exception:
            pass
    return "UTC"


def _to_local_date(dt: datetime, tz_name: str) -> date:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(ZoneInfo(tz_name)).date()


def _collect_active_dates(dates: Iterable[datetime], tz_name: str) -> set[date]:
    return {_to_local_date(dt, tz_name) for dt in dates if dt is not None}


def _current_streak(sorted_dates: list[date], today: date) -> int:
    if not sorted_dates:
        return 0
    anchor = today if today in sorted_dates else (today - timedelta(days=1))
    if anchor not in sorted_dates:
        return 0
    streak = 0
    cursor = anchor
    date_set = set(sorted_dates)
    while cursor in date_set:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def _longest_streak(sorted_dates: list[date]) -> int:
    if not sorted_dates:
        return 0
    best = 1
    run = 1
    for i in range(1, len(sorted_dates)):
        if sorted_dates[i] == sorted_dates[i - 1] + timedelta(days=1):
            run += 1
            best = max(best, run)
        else:
            run = 1
    return best


class StreakService:
    @staticmethod
    def get_streak(db: Session, user_id: int, *, timezone: str | None = None) -> StreakResponse:
        tz_name = _resolve_timezone(db, user_id, timezone)
        today = datetime.now(ZoneInfo(tz_name)).date()

        wore_rows = (
            db.query(OutfitFeedback.created_at)
            .filter(OutfitFeedback.user_id == user_id, OutfitFeedback.signal == SIGNAL_WORE)
            .all()
        )
        post_rows = (
            db.query(SocialPost.created_at).filter(SocialPost.user_id == user_id).all()
        )
        active = _collect_active_dates([r[0] for r in wore_rows], tz_name)
        active |= _collect_active_dates([r[0] for r in post_rows], tz_name)
        sorted_dates = sorted(active)

        week_start = today - timedelta(days=6)
        active_this_week = sum(1 for d in sorted_dates if week_start <= d <= today)

        last_active = sorted_dates[-1] if sorted_dates else None
        current = _current_streak(sorted_dates, today)

        return StreakResponse(
            current_streak=current,
            longest_streak=_longest_streak(sorted_dates),
            total_fit_days=len(sorted_dates),
            active_this_week=active_this_week,
            last_active_date=last_active,
            timezone=tz_name,
        )

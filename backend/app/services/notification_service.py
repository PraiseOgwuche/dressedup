"""Morning push notifications via the Expo Push API (free, no FCM/APNs keys)."""

import logging
from datetime import date, datetime, timezone
from typing import List, Optional
from zoneinfo import ZoneInfo

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models.daily_routine import DailyRoutine
from app.models.push_token import PushToken
from app.services.routine_service import RoutineService

logger = logging.getLogger(__name__)

_EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"


def _parse_wake_time(value: str) -> tuple[int, int]:
    try:
        hour_str, minute_str = value.strip().split(":", 1)
        hour = int(hour_str)
        minute = int(minute_str)
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return hour, minute
    except (ValueError, AttributeError):
        pass
    return 7, 0


def _item_name(item) -> Optional[str]:
    if not item:
        return None
    if isinstance(item, dict):
        return item.get("name")
    return getattr(item, "name", None)


def plan_notification_text(plan: dict) -> tuple[str, str]:
    activities = plan.get("activities") or []
    wear = next((a for a in activities if a.get("mode") == "wear"), None)
    packs = [a for a in activities if a.get("mode") == "pack"]
    title = "Your outfit for today"
    if not wear:
        return title, "Open DressedUp to see your plan."

    names = [
        name
        for slot in ("top", "bottom", "shoes")
        for name in [_item_name(wear.get(slot))]
        if name
    ]
    body = f"Wear: {', '.join(names)}" if names else f"Wear: {wear.get('title', 'your look')}"
    if packs:
        suffix = "s" if len(packs) > 1 else ""
        body += f". Pack for {len(packs)} stop{suffix} after."
    return title, body


class NotificationService:
    @staticmethod
    def register_token(
        db: Session,
        user_id: int,
        token: str,
        *,
        platform: Optional[str] = None,
        timezone_name: str = "UTC",
    ) -> PushToken:
        existing = db.query(PushToken).filter(PushToken.token == token).first()
        if existing:
            existing.user_id = user_id
            existing.platform = platform
            existing.timezone = timezone_name or "UTC"
            db.commit()
            db.refresh(existing)
            return existing

        row = PushToken(
            user_id=user_id,
            token=token,
            platform=platform,
            timezone=timezone_name or "UTC",
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    @staticmethod
    def unregister_token(db: Session, user_id: int, token: str) -> None:
        db.query(PushToken).filter(PushToken.user_id == user_id, PushToken.token == token).delete()
        db.commit()

    @staticmethod
    def send_expo_push(
        tokens: List[str],
        title: str,
        body: str,
        data: Optional[dict] = None,
    ) -> dict:
        if not tokens:
            return {"ok": True, "skipped": "no_tokens"}

        messages = [
            {
                "to": token,
                "title": title,
                "body": body,
                "sound": "default",
                "data": data or {"screen": "home"},
            }
            for token in tokens
        ]
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if settings.EXPO_ACCESS_TOKEN:
            headers["Authorization"] = f"Bearer {settings.EXPO_ACCESS_TOKEN}"

        with httpx.Client(timeout=15.0) as client:
            response = client.post(_EXPO_PUSH_URL, json=messages, headers=headers)
            response.raise_for_status()
            return response.json()

    @staticmethod
    def send_today_plan_to_user(db: Session, user_id: int) -> dict:
        plan = RoutineService.today_plan(db, user_id)
        title, body = plan_notification_text(plan)
        tokens = [row.token for row in db.query(PushToken).filter(PushToken.user_id == user_id).all()]
        result = NotificationService.send_expo_push(tokens, title, body, data={"screen": "home", "source": "routine"})
        return {"plan": plan, "push_result": result, "tokens_sent": len(tokens)}

    @staticmethod
    def routines_due_now(db: Session, now_utc: Optional[datetime] = None) -> List[DailyRoutine]:
        now_utc = now_utc or datetime.now(timezone.utc)
        routines = (
            db.query(DailyRoutine)
            .filter(DailyRoutine.enabled.is_(True), DailyRoutine.notifications_enabled.is_(True))
            .all()
        )
        due: List[DailyRoutine] = []
        for routine in routines:
            tz_name = routine.timezone or "UTC"
            try:
                local_now = now_utc.astimezone(ZoneInfo(tz_name))
            except Exception:
                local_now = now_utc.astimezone(ZoneInfo("UTC"))
            wake_hour, wake_minute = _parse_wake_time(routine.wake_time)
            if local_now.hour != wake_hour or local_now.minute != wake_minute:
                continue
            if routine.last_morning_push_at == local_now.date():
                continue
            due.append(routine)
        return due

    @staticmethod
    def process_morning_notifications(db: Session, now_utc: Optional[datetime] = None) -> int:
        sent = 0
        for routine in NotificationService.routines_due_now(db, now_utc=now_utc):
            tokens = [row.token for row in db.query(PushToken).filter(PushToken.user_id == routine.user_id).all()]
            if not tokens:
                continue
            try:
                plan = RoutineService.today_plan(db, routine.user_id)
                title, body = plan_notification_text(plan)
                NotificationService.send_expo_push(tokens, title, body)
                tz_name = routine.timezone or "UTC"
                try:
                    local_today = (now_utc or datetime.now(timezone.utc)).astimezone(ZoneInfo(tz_name)).date()
                except Exception:
                    local_today = date.today()
                routine.last_morning_push_at = local_today
                db.commit()
                sent += 1
            except Exception:
                logger.exception("failed morning push for user_id=%s", routine.user_id)
                db.rollback()
        return sent

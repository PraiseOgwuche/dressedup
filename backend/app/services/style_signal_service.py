"""Phase 1: unified style activity logging for personalization."""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.style_signal import StyleSignal

ALLOWED_EVENTS = frozenset(
    {
        "like",
        "dislike",
        "wore",
        "swap",
        "shop_tap",
        "shop_preview",
        "feed_share",
        "feed_like",
    }
)

EVENT_WEIGHTS: dict[str, float] = {
    "wore": 3.0,
    "like": 2.5,
    "feed_share": 2.0,
    "swap": 1.5,
    "shop_preview": 1.2,
    "shop_tap": 0.8,
    "feed_like": 0.6,
    "dislike": -3.0,
}

_RECENCY_HALF_LIFE_DAYS = 45.0


class StyleSignalService:
    @staticmethod
    def event_weight(event_type: str) -> float:
        return EVENT_WEIGHTS.get(event_type, 0.0)

    @staticmethod
    def recency_multiplier(created_at: datetime | None, *, now: datetime | None = None) -> float:
        if created_at is None:
            return 1.0
        now = now or datetime.now(timezone.utc)
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        age_days = max(0.0, (now - created_at).total_seconds() / 86400.0)
        return math.exp(-age_days / _RECENCY_HALF_LIFE_DAYS)

    @staticmethod
    def weighted_value(event_type: str, created_at: datetime | None) -> float:
        return StyleSignalService.event_weight(event_type) * StyleSignalService.recency_multiplier(created_at)

    @classmethod
    def record(
        cls,
        db: Session,
        user_id: int,
        event_type: str,
        *,
        top_id: Optional[int] = None,
        bottom_id: Optional[int] = None,
        shoes_id: Optional[int] = None,
        outerwear_id: Optional[int] = None,
        dress_id: Optional[int] = None,
        swap_slot: Optional[str] = None,
        replaced_item_id: Optional[int] = None,
        product_id: Optional[str] = None,
        post_id: Optional[int] = None,
        occasion: Optional[str] = None,
        weather_tag: Optional[str] = None,
        commit: bool = True,
    ) -> StyleSignal:
        if event_type not in ALLOWED_EVENTS:
            raise ValueError(f"Unknown event_type: {event_type}")

        entry = StyleSignal(
            user_id=user_id,
            event_type=event_type,
            top_id=top_id,
            bottom_id=bottom_id,
            shoes_id=shoes_id,
            outerwear_id=outerwear_id,
            dress_id=dress_id,
            swap_slot=swap_slot,
            replaced_item_id=replaced_item_id,
            product_id=product_id,
            post_id=post_id,
            occasion=occasion,
            weather_tag=weather_tag,
        )
        db.add(entry)
        if commit:
            db.commit()
            db.refresh(entry)
        return entry

    @staticmethod
    def recent(db: Session, user_id: int, *, limit: int = 200) -> list[StyleSignal]:
        return (
            db.query(StyleSignal)
            .filter(StyleSignal.user_id == user_id)
            .order_by(StyleSignal.created_at.desc())
            .limit(limit)
            .all()
        )

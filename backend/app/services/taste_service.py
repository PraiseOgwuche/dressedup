"""Outfit Engine v4 Phase 8 — embedding-space taste centroids.

Builds positive and negative taste vectors from real behavior (wears, likes,
dislikes, swaps, feed/shop signals), using the same 45-day recency decay as
StyleSignalService. Combined with the structured PreferenceService model.

Cold start: until enough positively-weighted *embedded* items exist, the
taste signal is zero — new users stay fully rule-driven. Confidence then
ramps linearly so personalization grows rather than jumping in.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

import numpy as np
from sqlalchemy.orm import Session

from app.config import settings
from app.models.clothing_item import ClothingItem
from app.models.style_signal import StyleSignal
from app.services.retrieval_service import item_vector
from app.services.style_signal_service import StyleSignalService

# Need this many distinct positively-weighted embedded items before taste speaks.
_MIN_POSITIVE_ITEMS = 3
# At this many, the ramp reaches 1.0 (full taste weight).
_FULL_CONFIDENCE_ITEMS = 9

# Events that push an item toward the positive centroid (beyond weight sign).
_POSITIVE_EVENTS = frozenset(
    {"wore", "like", "swap", "feed_share", "feed_like", "shop_tap", "shop_preview"}
)
_NEGATIVE_EVENTS = frozenset({"dislike"})


def _item_ids_from_signal(signal: StyleSignal) -> list[int]:
    return [
        i
        for i in (
            signal.top_id,
            signal.bottom_id,
            signal.shoes_id,
            signal.outerwear_id,
            signal.dress_id,
        )
        if i
    ]


def _load_items(db: Session, user_id: int, item_ids: set[int]) -> dict[int, ClothingItem]:
    if not item_ids:
        return {}
    rows = (
        db.query(ClothingItem)
        .filter(ClothingItem.user_id == user_id, ClothingItem.id.in_(item_ids))
        .all()
    )
    return {row.id: row for row in rows}


@dataclass(frozen=True)
class TasteProfile:
    positive: Optional[np.ndarray]
    negative: Optional[np.ndarray]
    positive_count: int
    negative_count: int
    confidence: float  # [0, 1] — 0 means cold-start / unused

    @property
    def ready(self) -> bool:
        return self.confidence > 0.0 and self.positive is not None


def _normalize(vector: np.ndarray) -> Optional[np.ndarray]:
    norm = float(np.linalg.norm(vector))
    if norm < 1e-8:
        return None
    return vector / norm


def _weighted_centroid(
    weighted: list[tuple[np.ndarray, float]],
) -> Optional[np.ndarray]:
    if not weighted:
        return None
    total_w = sum(abs(w) for _, w in weighted)
    if total_w < 1e-8:
        return None
    mean = sum(v * abs(w) for v, w in weighted) / total_w
    return _normalize(np.asarray(mean, dtype=np.float32))


class TasteService:
    @staticmethod
    def confidence_from_count(positive_count: int) -> float:
        """Gradual ramp: 0 below the floor, 1.0 at full confidence."""
        if positive_count < _MIN_POSITIVE_ITEMS:
            return 0.0
        span = _FULL_CONFIDENCE_ITEMS - _MIN_POSITIVE_ITEMS
        return min(1.0, (positive_count - _MIN_POSITIVE_ITEMS + 1) / (span + 1))

    @classmethod
    def build_profile(
        cls,
        db: Session,
        user_id: int,
        *,
        signals: Sequence[StyleSignal] | None = None,
    ) -> TasteProfile:
        """Positive/negative centroids over recent style signals (recency-decayed)."""
        empty = TasteProfile(None, None, 0, 0, 0.0)
        if not settings.OUTFIT_EMBEDDINGS_ENABLED:
            return empty

        rows = list(signals) if signals is not None else StyleSignalService.recent(db, user_id, limit=200)
        if not rows:
            return empty

        history_ids: set[int] = set()
        for signal in rows:
            history_ids.update(_item_ids_from_signal(signal))
            if signal.replaced_item_id:
                history_ids.add(signal.replaced_item_id)
        history = _load_items(db, user_id, history_ids)

        pos_acc: dict[int, float] = {}
        neg_acc: dict[int, float] = {}

        for signal in rows:
            weight = StyleSignalService.weighted_value(signal.event_type, signal.created_at)
            if weight == 0:
                continue
            ids = _item_ids_from_signal(signal)

            if signal.event_type in _NEGATIVE_EVENTS or weight < 0:
                for item_id in ids:
                    neg_acc[item_id] = neg_acc.get(item_id, 0.0) + abs(weight)
            elif signal.event_type in _POSITIVE_EVENTS:
                for item_id in ids:
                    pos_acc[item_id] = pos_acc.get(item_id, 0.0) + abs(weight)
                # Swapped-out piece is a soft negative — user rejected it for this look.
                if signal.event_type == "swap" and signal.replaced_item_id:
                    neg_acc[signal.replaced_item_id] = (
                        neg_acc.get(signal.replaced_item_id, 0.0) + abs(weight) * 0.4
                    )

        def collect(acc: dict[int, float]) -> list[tuple[np.ndarray, float]]:
            out: list[tuple[np.ndarray, float]] = []
            for item_id, w in acc.items():
                item = history.get(item_id)
                if item is None:
                    continue
                vector = item_vector(item)
                if vector is None:
                    continue
                out.append((vector, w))
            return out

        pos_weighted = collect(pos_acc)
        neg_weighted = collect(neg_acc)
        positive = _weighted_centroid(pos_weighted)
        negative = _weighted_centroid(neg_weighted)
        positive_count = len(pos_weighted)
        negative_count = len(neg_weighted)
        confidence = cls.confidence_from_count(positive_count)

        return TasteProfile(
            positive=positive,
            negative=negative,
            positive_count=positive_count,
            negative_count=negative_count,
            confidence=confidence,
        )

    @staticmethod
    def item_affinity(item: ClothingItem, profile: TasteProfile) -> float:
        """How well one garment matches taste, in [-1, 1], before confidence scaling."""
        if not profile.ready or profile.positive is None:
            return 0.0
        vector = item_vector(item)
        if vector is None:
            return 0.0
        pos = float(vector @ profile.positive)
        if profile.negative is not None:
            neg = float(vector @ profile.negative)
            # Prefer pieces near the liked look and away from disliked look.
            raw = pos - 0.65 * neg
        else:
            raw = pos
        return max(-1.0, min(1.0, raw))

    @classmethod
    def score_outfit(
        cls,
        db: Session,
        user_id: int,
        garments: Sequence[ClothingItem],
        *,
        profile: TasteProfile | None = None,
    ) -> tuple[float, list[str]]:
        """(taste bonus in [-1, 1], notes). Zero when cold-start or embeddings off."""
        garments = [g for g in garments if g is not None]
        if not garments or not settings.OUTFIT_EMBEDDINGS_ENABLED:
            return 0.0, []

        profile = profile or cls.build_profile(db, user_id)
        if not profile.ready:
            return 0.0, []

        scores = [cls.item_affinity(g, profile) for g in garments]
        embedded = [s for s, g in zip(scores, garments) if item_vector(g) is not None]
        if not embedded:
            return 0.0, []

        raw = sum(embedded) / len(embedded)
        scaled = max(-1.0, min(1.0, raw * profile.confidence))

        notes: list[str] = []
        if scaled > 0.28:
            notes.append("matches looks you've liked")
        elif scaled < -0.28:
            notes.append("drifts from what you usually prefer")
        return scaled, notes

    @classmethod
    def retrieval_query(
        cls,
        db: Session,
        user_id: int,
        fallback: Optional[np.ndarray],
    ) -> Optional[np.ndarray]:
        """Prefer the positive taste centroid for hybrid retrieval when confident."""
        if not settings.OUTFIT_EMBEDDINGS_ENABLED:
            return fallback
        profile = cls.build_profile(db, user_id)
        if not profile.ready or profile.positive is None:
            return fallback
        if fallback is None:
            return profile.positive
        # Blend: more taste as confidence grows, still anchored to closet look.
        blended = profile.confidence * profile.positive + (1.0 - profile.confidence) * fallback
        normalized = _normalize(np.asarray(blended, dtype=np.float32))
        return normalized if normalized is not None else fallback

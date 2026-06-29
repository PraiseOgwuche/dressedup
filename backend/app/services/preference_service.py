"""Layer 2: learn what each user actually likes from explicit feedback and wears."""

from __future__ import annotations

from collections import defaultdict
from itertools import combinations
from typing import TYPE_CHECKING, Optional

from sqlalchemy.orm import Session

from app.fashion.color_harmony import color_family, normalize_color_name
from app.models.outfit_feedback import SIGNAL_DISLIKE, SIGNAL_LIKE, SIGNAL_WORE, OutfitFeedback
from app.taxonomy import FORMALITY_LEVELS

if TYPE_CHECKING:
    from app.models.clothing_item import ClothingItem

_FORMALITY_INDEX = {level: i for i, level in enumerate(FORMALITY_LEVELS)}

_SIGNAL_LABELS = {
    "like": SIGNAL_LIKE,
    "dislike": SIGNAL_DISLIKE,
    "wore": SIGNAL_WORE,
}


class PreferenceService:
    @staticmethod
    def signal_value(label: str) -> int:
        value = _SIGNAL_LABELS.get(label)
        if value is None:
            raise ValueError(f"Unknown signal: {label}")
        return value

    @staticmethod
    def record(
        db: Session,
        user_id: int,
        *,
        top_id: Optional[int],
        bottom_id: Optional[int],
        shoes_id: Optional[int],
        outerwear_id: Optional[int] = None,
        signal: str,
        occasion: Optional[str] = None,
        weather_tag: Optional[str] = None,
    ) -> OutfitFeedback:
        entry = OutfitFeedback(
            user_id=user_id,
            top_id=top_id,
            bottom_id=bottom_id,
            shoes_id=shoes_id,
            outerwear_id=outerwear_id,
            signal=PreferenceService.signal_value(signal),
            occasion=occasion,
            weather_tag=weather_tag,
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry

    @staticmethod
    def personalization_bonus(
        db: Session,
        user_id: int,
        garments: list[ClothingItem],
    ) -> tuple[float, list[str]]:
        """Return a normalized bonus in [-1, 1] and human notes for rationale."""
        garments = [g for g in garments if g is not None]
        if not garments:
            return 0.0, []

        feedback = (
            db.query(OutfitFeedback)
            .filter(OutfitFeedback.user_id == user_id)
            .order_by(OutfitFeedback.created_at.desc())
            .limit(80)
            .all()
        )
        if not feedback:
            return 0.0, []

        item_ids = {g.id for g in garments}
        pair_weights: dict[frozenset[int], float] = defaultdict(float)
        color_weights: dict[str, float] = defaultdict(float)
        formality_samples: list[int] = []

        for entry in feedback:
            ids = [i for i in (entry.top_id, entry.bottom_id, entry.shoes_id, entry.outerwear_id) if i]
            weight = entry.signal / 3.0
            for a, b in combinations(ids, 2):
                pair_weights[frozenset({a, b})] += weight

        for entry in feedback:
            if entry.signal <= 0:
                continue
            for item_id in (entry.top_id, entry.bottom_id, entry.shoes_id, entry.outerwear_id):
                if not item_id:
                    continue
                garment = next((g for g in garments if g.id == item_id), None)
                if garment and garment.color:
                    color_weights[normalize_color_name(garment.color)] += entry.signal / 3.0

        # Pair affinity — have we liked/worn this combo before?
        pair_bonus = 0.0
        for a, b in combinations(item_ids, 2):
            pair_bonus += pair_weights.get(frozenset({a, b}), 0.0)
        pair_bonus = max(-1.0, min(1.0, pair_bonus / 3.0))

        # Color preference — does this outfit use colors the user gravitates toward?
        color_bonus = 0.0
        for garment in garments:
            if not garment.color:
                continue
            color_bonus += color_weights.get(normalize_color_name(garment.color), 0.0)
        color_bonus = max(-1.0, min(1.0, color_bonus / 4.0))

        # Formality comfort zone from positive history
        positive_entries = [e for e in feedback if e.signal > 0]
        for entry in positive_entries[:40]:
            # Approximate from stored item ids — load minimal attrs from current garments if overlap
            overlap = item_ids & {entry.top_id, entry.bottom_id, entry.shoes_id, entry.outerwear_id}
            for garment in garments:
                if garment.id in overlap and garment.formality in _FORMALITY_INDEX:
                    formality_samples.append(_FORMALITY_INDEX[garment.formality])

        formality_bonus = 0.0
        if formality_samples and garments:
            target = sum(formality_samples) / len(formality_samples)
            current = [
                _FORMALITY_INDEX[g.formality]
                for g in garments
                if g.formality in _FORMALITY_INDEX
            ]
            if current:
                avg = sum(current) / len(current)
                distance = abs(avg - target)
                formality_bonus = max(0.0, 0.6 - distance * 0.2)

        total = pair_bonus * 0.5 + color_bonus * 0.25 + formality_bonus * 0.25
        total = max(-1.0, min(1.0, total))

        notes: list[str] = []
        if pair_bonus > 0.35:
            notes.append("you've worn this combo before")
        elif color_bonus > 0.35:
            families = {color_family(g.color) for g in garments if g.color}
            if "neutral" not in families and families:
                notes.append("colors you usually pick")

        return total, notes

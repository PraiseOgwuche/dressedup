"""Layer 2: learn what each user actually likes from activity signals."""

from __future__ import annotations

from collections import defaultdict
from itertools import combinations
from typing import TYPE_CHECKING, Optional

from sqlalchemy.orm import Session

from app.fashion.color_harmony import color_family, normalize_color_name
from app.models.clothing_item import ClothingItem
from app.models.outfit_feedback import SIGNAL_DISLIKE, SIGNAL_LIKE, SIGNAL_WORE, OutfitFeedback
from app.models.style_signal import StyleSignal
from app.services.style_signal_service import StyleSignalService
from app.shop.catalog import load_catalog
from app.taxonomy import FORMALITY_LEVELS

if TYPE_CHECKING:
    pass

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
        dress_id: Optional[int] = None,
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
            dress_id=dress_id,
            signal=PreferenceService.signal_value(signal),
            occasion=occasion,
            weather_tag=weather_tag,
        )
        db.add(entry)
        db.flush()
        StyleSignalService.record(
            db,
            user_id,
            signal,
            top_id=top_id,
            bottom_id=bottom_id,
            shoes_id=shoes_id,
            outerwear_id=outerwear_id,
            dress_id=dress_id,
            occasion=occasion,
            weather_tag=weather_tag,
            commit=False,
        )
        db.commit()
        db.refresh(entry)
        return entry

    @staticmethod
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

    @staticmethod
    def _load_history_items(db: Session, user_id: int, item_ids: set[int]) -> dict[int, ClothingItem]:
        if not item_ids:
            return {}
        rows = (
            db.query(ClothingItem)
            .filter(ClothingItem.user_id == user_id, ClothingItem.id.in_(item_ids))
            .all()
        )
        return {row.id: row for row in rows}

    @classmethod
    def personalization_bonus(
        cls,
        db: Session,
        user_id: int,
        garments: list[ClothingItem],
    ) -> tuple[float, list[str]]:
        """Return a normalized bonus in [-1, 1] and human notes for rationale."""
        garments = [g for g in garments if g is not None]
        if not garments:
            return 0.0, []

        signals = StyleSignalService.recent(db, user_id, limit=200)
        if not signals:
            return 0.0, []

        item_ids = {g.id for g in garments}
        catalog_by_id = {product.id: product for product in load_catalog()}

        pair_weights: dict[frozenset[int], float] = defaultdict(float)
        item_weights: dict[int, float] = defaultdict(float)
        color_weights: dict[str, float] = defaultdict(float)
        category_weights: dict[str, float] = defaultdict(float)
        subcategory_weights: dict[str, float] = defaultdict(float)
        occasion_weights: dict[str, float] = defaultdict(float)
        swap_in_weights: dict[int, float] = defaultdict(float)
        swap_out_weights: dict[int, float] = defaultdict(float)
        shop_color_weights: dict[str, float] = defaultdict(float)
        shop_category_weights: dict[str, float] = defaultdict(float)
        formality_samples: list[int] = []

        history_ids: set[int] = set()
        for signal in signals:
            history_ids.update(cls._item_ids_from_signal(signal))
            if signal.replaced_item_id:
                history_ids.add(signal.replaced_item_id)

        history_items = cls._load_history_items(db, user_id, history_ids)

        for signal in signals:
            weight = StyleSignalService.weighted_value(signal.event_type, signal.created_at)
            if weight == 0:
                continue

            ids = cls._item_ids_from_signal(signal)
            for item_id in ids:
                item_weights[item_id] += weight
            for a, b in combinations(ids, 2):
                pair_weights[frozenset({a, b})] += weight

            if signal.event_type == "swap" and signal.replaced_item_id:
                swap_out_weights[signal.replaced_item_id] += abs(weight) * 0.35
                for item_id in ids:
                    swap_in_weights[item_id] += weight

            if signal.occasion and weight > 0:
                occasion_weights[signal.occasion.lower()] += weight

            if weight <= 0:
                continue

            for item_id in ids:
                historical = history_items.get(item_id)
                if not historical:
                    continue
                if historical.color:
                    color_weights[normalize_color_name(historical.color)] += weight
                if historical.category:
                    category_weights[historical.category.lower()] += weight
                if historical.subcategory:
                    subcategory_weights[historical.subcategory.lower()] += weight
                if historical.formality in _FORMALITY_INDEX:
                    formality_samples.append(_FORMALITY_INDEX[historical.formality])

            if signal.product_id and signal.event_type in {"shop_tap", "shop_preview"}:
                product = catalog_by_id.get(signal.product_id)
                if product:
                    if product.color:
                        shop_color_weights[normalize_color_name(product.color)] += weight
                    shop_category_weights[product.category.lower()] += weight

        def clamp(value: float, cap: float = 1.0) -> float:
            return max(-cap, min(cap, value))

        pair_bonus = 0.0
        for a, b in combinations(item_ids, 2):
            pair_bonus += pair_weights.get(frozenset({a, b}), 0.0)
        pair_bonus = clamp(pair_bonus / 4.0)

        item_bonus = sum(item_weights.get(g.id, 0.0) for g in garments)
        item_bonus = clamp(item_bonus / 5.0)

        color_bonus = 0.0
        for garment in garments:
            if garment.color:
                color_bonus += color_weights.get(normalize_color_name(garment.color), 0.0)
                color_bonus += shop_color_weights.get(normalize_color_name(garment.color), 0.0) * 0.6
        color_bonus = clamp(color_bonus / 5.0)

        category_bonus = 0.0
        for garment in garments:
            if garment.category:
                category_bonus += category_weights.get(garment.category.lower(), 0.0)
                category_bonus += shop_category_weights.get(garment.category.lower(), 0.0) * 0.5
            if garment.subcategory:
                category_bonus += subcategory_weights.get(garment.subcategory.lower(), 0.0) * 0.7
        category_bonus = clamp(category_bonus / 6.0)

        swap_bonus = 0.0
        for garment in garments:
            swap_bonus += swap_in_weights.get(garment.id, 0.0)
            swap_bonus -= swap_out_weights.get(garment.id, 0.0)
        swap_bonus = clamp(swap_bonus / 3.0)

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
                formality_bonus = max(0.0, 0.75 - distance * 0.22)

        occasion_bonus = 0.0
        garment_occasions: set[str] = set()
        for garment in garments:
            for tag in garment.occasion or []:
                garment_occasions.add(tag.lower())
        if garment_occasions and occasion_weights:
            overlap = sum(occasion_weights.get(tag, 0.0) for tag in garment_occasions)
            occasion_bonus = clamp(overlap / 6.0, cap=0.6)

        total = (
            pair_bonus * 0.22
            + item_bonus * 0.18
            + color_bonus * 0.16
            + category_bonus * 0.12
            + swap_bonus * 0.12
            + formality_bonus * 0.12
            + occasion_bonus * 0.08
        )
        total = clamp(total)

        notes: list[str] = []
        if pair_bonus > 0.25:
            notes.append("you've worn this combo before")
        elif item_bonus > 0.28:
            notes.append("pieces you reach for often")
        elif swap_bonus > 0.2:
            notes.append("similar to swaps you've chosen")
        elif color_bonus > 0.28:
            families = {color_family(g.color) for g in garments if g.color}
            if "neutral" not in families and families:
                notes.append("colors you usually pick")
        elif category_bonus > 0.22:
            notes.append("fits your go-to categories")
        elif shop_color_weights and color_bonus > 0.15:
            notes.append("aligned with shop picks you've explored")

        return total, notes

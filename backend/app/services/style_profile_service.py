"""Aggregate closet + style signals into a visible style profile."""

from __future__ import annotations

from collections import Counter
from typing import Optional

from sqlalchemy.orm import Session

from app.fashion.color_harmony import normalize_color_name
from app.models.clothing_item import ClothingItem
from app.services.style_signal_service import StyleSignalService
from app.taxonomy import FORMALITY_LEVELS

_FORMALITY_INDEX = {level: i for i, level in enumerate(FORMALITY_LEVELS)}

_POSITIVE_EVENTS = frozenset({"wore", "like", "feed_share", "feed_like", "swap", "shop_preview"})


class StyleProfileService:
    @classmethod
    def get_profile(cls, db: Session, user_id: int) -> dict:
        items = db.query(ClothingItem).filter(ClothingItem.user_id == user_id).all()
        signals = StyleSignalService.recent(db, user_id, limit=200)

        color_counts: Counter[str] = Counter()
        category_counts: Counter[str] = Counter()
        occasion_counts: Counter[str] = Counter()
        formality_samples: list[int] = []
        item_by_id = {item.id: item for item in items}

        for item in items:
            cat = (item.category or "unknown").lower()
            category_counts[cat] += 1
            if item.color:
                color_counts[normalize_color_name(item.color)] += 1

        activity = {
            "wore": 0,
            "likes": 0,
            "swaps": 0,
            "shop_explores": 0,
            "feed_shares": 0,
        }

        for signal in signals:
            if signal.event_type == "wore":
                activity["wore"] += 1
            elif signal.event_type == "like":
                activity["likes"] += 1
            elif signal.event_type == "swap":
                activity["swaps"] += 1
            elif signal.event_type in {"shop_tap", "shop_preview"}:
                activity["shop_explores"] += 1
            elif signal.event_type == "feed_share":
                activity["feed_shares"] += 1

            if signal.event_type not in _POSITIVE_EVENTS:
                continue

            if signal.occasion:
                occasion_counts[signal.occasion.lower()] += 1

            for item_id in (
                signal.top_id,
                signal.bottom_id,
                signal.shoes_id,
                signal.outerwear_id,
            ):
                if not item_id:
                    continue
                garment = item_by_id.get(item_id)
                if not garment:
                    continue
                if garment.color:
                    color_counts[normalize_color_name(garment.color)] += 2
                if garment.formality in _FORMALITY_INDEX:
                    formality_samples.append(_FORMALITY_INDEX[garment.formality])

        top_colors = [
            {"label": name.title(), "value": count}
            for name, count in color_counts.most_common(5)
            if name
        ]
        top_categories = [
            {"label": name.replace("-", " ").title(), "value": count}
            for name, count in category_counts.most_common(4)
        ]
        top_occasions = [name for name, _ in occasion_counts.most_common(3)]

        formality_zone: Optional[str] = None
        if formality_samples:
            avg = sum(formality_samples) / len(formality_samples)
            formality_zone = FORMALITY_LEVELS[min(round(avg), len(FORMALITY_LEVELS) - 1)]

        insights = cls._insights(
            top_colors=top_colors,
            top_categories=top_categories,
            formality_zone=formality_zone,
            top_occasions=top_occasions,
            activity=activity,
            signal_count=len(signals),
            clean_count=sum(1 for i in items if i.is_clean),
        )

        summary = cls._summary(
            signal_count=len(signals),
            top_colors=top_colors,
            formality_zone=formality_zone,
            activity=activity,
        )

        return {
            "headline": "Your style profile",
            "summary": summary,
            "top_colors": top_colors,
            "top_categories": top_categories,
            "formality_zone": formality_zone,
            "top_occasions": top_occasions,
            "activity": activity,
            "insights": insights,
            "signal_count": len(signals),
        }

    @staticmethod
    def _summary(
        *,
        signal_count: int,
        top_colors: list[dict],
        formality_zone: Optional[str],
        activity: dict,
    ) -> str:
        if signal_count < 3:
            return "Wear, swap, and like outfits — we'll learn your taste as you go."
        parts: list[str] = []
        if top_colors:
            parts.append(f"gravitating toward {top_colors[0]['label'].lower()}")
        if formality_zone:
            parts.append(f"{formality_zone.replace('-', ' ')} comfort zone")
        if activity["swaps"] >= 2:
            parts.append("you refine looks with swaps")
        if not parts:
            return "Building your style fingerprint from wears and picks."
        return "We're learning you — " + ", ".join(parts) + "."

    @staticmethod
    def _insights(
        *,
        top_colors: list[dict],
        top_categories: list[dict],
        formality_zone: Optional[str],
        top_occasions: list[str],
        activity: dict,
        signal_count: int,
        clean_count: int,
    ) -> list[str]:
        insights: list[str] = []

        if signal_count < 2:
            insights.append("Log a few wears on Home to unlock personalized picks.")
            if clean_count < 5:
                insights.append("Add more closet pieces for richer outfit suggestions.")
            return insights[:3]

        if top_colors:
            leader = top_colors[0]["label"]
            insights.append(f"You lean toward {leader.lower()} in your rotation.")

        if top_categories:
            cat = top_categories[0]["label"].lower()
            insights.append(f"Most of your closet is {cat} — we weight suggestions accordingly.")

        if formality_zone:
            insights.append(f"Your sweet spot is {formality_zone.replace('-', ' ')} dressing.")

        if activity["swaps"] >= 2:
            insights.append("Swap history helps us suggest pieces you'll actually keep.")

        if top_occasions:
            insights.append(f"Often dressing for {top_occasions[0].replace('-', ' ')}.")

        if activity["shop_explores"] >= 2:
            insights.append("Shop picks you explore nudge future outfit scores.")

        return insights[:4]

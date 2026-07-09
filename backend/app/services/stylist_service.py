"""Phase 4 — LLM stylist layer on top of rule engine + personalization."""

from __future__ import annotations

from collections import Counter
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.fashion.knowledge import gap_priorities
from app.models.clothing_item import ClothingItem
from app.services.stylist import get_stylist


class StylistService:
    @staticmethod
    def _serialize_garment(item: ClothingItem | None) -> Optional[dict[str, Any]]:
        if item is None:
            return None
        return {
            "name": item.name,
            "category": item.category,
            "subcategory": item.subcategory,
            "color": item.color,
            "formality": item.formality,
            "pattern": item.pattern,
            "material": item.material,
        }

    @classmethod
    def closet_snapshot(cls, db: Session, user_id: int) -> dict[str, Any]:
        items = (
            db.query(ClothingItem)
            .filter(ClothingItem.user_id == user_id, ClothingItem.is_clean.is_(True))
            .all()
        )
        by_category: Counter[str] = Counter()
        colors: Counter[str] = Counter()
        for item in items:
            by_category[(item.category or "unknown").lower()] += 1
            if item.color:
                colors[item.color.lower()] += 1

        sample = [
            {
                "name": item.name,
                "category": item.category,
                "color": item.color,
                "formality": item.formality,
            }
            for item in items[:18]
        ]

        return {
            "clean_count": len(items),
            "by_category": dict(by_category),
            "top_colors": [color for color, _ in colors.most_common(6)],
            "sample_items": sample,
        }

    @staticmethod
    def rule_based_gap_insight(closet: dict[str, Any]) -> str:
        by_category = closet.get("by_category", {})
        for row in sorted(gap_priorities(), key=lambda r: -float(r.get("unlock_weight", 0))):
            category = row.get("category", "")
            if by_category.get(category, 0) < 2:
                return str(row.get("hint", "Add versatile basics to unlock more outfits."))
        return "Your closet has solid coverage — fresh picks can still add new combinations."

    @staticmethod
    def _gap_row_for_closet(closet: dict[str, Any]) -> Optional[dict[str, Any]]:
        by_category = closet.get("by_category", {})
        for row in sorted(gap_priorities(), key=lambda r: -float(r.get("unlock_weight", 0))):
            category = str(row.get("category", ""))
            count = int(by_category.get(category, 0))
            if count < 2:
                return {**row, "category": category, "closet_count": count}
        return None

    @classmethod
    def build_gap_card(
        cls,
        closet: dict[str, Any],
        top_pick: Optional[dict[str, Any]],
    ) -> Optional[dict[str, Any]]:
        gap = cls._gap_row_for_closet(closet)
        if gap is None and not top_pick:
            return None

        category = gap["category"] if gap else (top_pick or {}).get("category", "")
        closet_count = gap["closet_count"] if gap else closet.get("by_category", {}).get(category, 0)
        reason = str(gap.get("hint") if gap else "A strong add can still unlock new combinations.")

        pick = top_pick
        if gap and top_pick and top_pick.get("category") != category:
            pick = top_pick

        titles = {
            "bottom": "Bottoms gap",
            "footwear": "Shoes gap",
            "top": "Tops gap",
            "outerwear": "Layer gap",
        }
        title = titles.get(category, f"{category.replace('-', ' ').title()} gap")

        return {
            "title": title,
            "category": category,
            "closet_count": closet_count,
            "reason": reason,
            "unlock_outfits": int((pick or {}).get("outfit_count", 0)),
            "product_id": (pick or {}).get("product_id"),
            "product_brand": (pick or {}).get("brand"),
            "product_name": (pick or {}).get("name"),
            "image_url": (pick or {}).get("image_url"),
            "price_usd": (pick or {}).get("price_usd"),
        }

    @classmethod
    def enhance_outfit(
        cls,
        db: Session,
        user_id: int,
        *,
        top,
        bottom,
        shoes,
        outerwear,
        occasion: Optional[str],
        weather_tag: Optional[str],
        trend: Optional[str],
        rule_rationale: Optional[str],
    ) -> Optional[str]:
        closet = cls.closet_snapshot(db, user_id)
        outfit = {
            "top": cls._serialize_garment(top),
            "bottom": cls._serialize_garment(bottom),
            "shoes": cls._serialize_garment(shoes),
            "outerwear": cls._serialize_garment(outerwear),
        }
        context = {
            "occasion": occasion,
            "weather_tag": weather_tag,
            "trend": trend,
        }
        provider = get_stylist()
        if not provider.available():
            return None
        return provider.outfit_note(
            closet=closet,
            outfit=outfit,
            context=context,
            rule_rationale=rule_rationale,
        )

    @classmethod
    def shop_insight(
        cls,
        db: Session,
        user_id: int,
        *,
        summary: str,
        top_pick: Optional[dict[str, Any]],
    ) -> str:
        closet = cls.closet_snapshot(db, user_id)
        provider = get_stylist()
        if provider.available():
            llm = provider.closet_gap_insight(
                closet=closet,
                shop_summary=summary,
                top_pick=top_pick,
            )
            if llm:
                return llm
        return cls.rule_based_gap_insight(closet)

"""Occasion color palettes and aesthetic trend profiles from knowledge.yaml."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from app.fashion.color_harmony import color_family, is_neutral_name, normalize_color_name
from app.fashion.knowledge import occasion_color_palettes, trend_profiles
from app.taxonomy import FORMALITY_LEVELS

if TYPE_CHECKING:
    from app.models.clothing_item import ClothingItem

_FORMALITY_INDEX = {level: i for i, level in enumerate(FORMALITY_LEVELS)}


def _color_in_palette(color: Optional[str], palette: set[str]) -> bool:
    name = normalize_color_name(color)
    if not name:
        return False
    if name in palette:
        return True
    if is_neutral_name(name) and any(n in palette for n in ("black", "white", "gray", "grey", "beige", "cream", "navy")):
        return True
    return any(token in name for token in palette) or any(name in token for token in palette)


def score_occasion_palette(
    garments: list[ClothingItem],
    occasion: Optional[str],
) -> tuple[float, list[str], list[str]]:
    """Bonus when outfit colors fit the occasion's recommended palette."""
    if not occasion:
        return 0.0, [], []

    palette = occasion_color_palettes().get(occasion)
    if not palette:
        return 0.0, [], []

    colored = [g for g in garments if g.color]
    if not colored:
        return 0.0, [], []

    hits = sum(1 for g in colored if _color_in_palette(g.color, palette))
    ratio = hits / len(colored)
    score = (ratio - 0.5) * 1.2  # neutral baseline 0.5 -> 0.0
    highlights: list[str] = []
    warnings: list[str] = []

    if ratio >= 0.75:
        highlights.append(f"colors fit {occasion}")
    elif ratio < 0.34:
        warnings.append(f"bold colors for {occasion}")

    return max(-1.0, min(1.0, score)), highlights, warnings


def _garment_trend_score(garment: ClothingItem, profile: dict[str, Any]) -> float:
    score = 0.0
    checks = 0

    formality = garment.formality
    allowed_formality = set(profile.get("formality", []))
    if formality and allowed_formality:
        checks += 1
        if formality in allowed_formality:
            score += 1.0
        else:
            score -= 0.4

    pattern = (garment.pattern or "solid").lower()
    preferred_patterns = set(profile.get("patterns", []))
    avoid_patterns = set(profile.get("avoid_patterns", []))
    if pattern:
        checks += 1
        if pattern in avoid_patterns:
            score -= 0.8
        elif preferred_patterns and pattern in preferred_patterns:
            score += 0.7
        elif pattern == "solid" and "solid" in preferred_patterns:
            score += 0.5

    palette = set(profile.get("colors", []))
    if garment.color and palette:
        checks += 1
        score += 0.8 if _color_in_palette(garment.color, palette) else -0.2

    material = (getattr(garment, "material", None) or "").lower()
    preferred_materials = profile.get("materials", [])
    if material and preferred_materials:
        checks += 1
        if any(token in material for token in preferred_materials):
            score += 0.6

    footwear_label = ((garment.subcategory or garment.category) or "").lower()
    preferred_footwear = set(profile.get("footwear", []))
    if footwear_label in {"footwear", "shoes", "sneakers", "boots", "heels", "sandals"} or footwear_label in preferred_footwear:
        if preferred_footwear and footwear_label in preferred_footwear:
            checks += 1
            score += 0.7

    style_tags = getattr(garment, "style_tags", None) or []
    trend_id = profile.get("_id")
    if trend_id and style_tags and trend_id in style_tags:
        score += 1.2
        checks += 1

    if checks == 0:
        return 0.0
    return score / checks


def score_trend_fit(
    garments: list[ClothingItem],
    trend: Optional[str],
) -> tuple[float, list[str], list[str]]:
    if not trend:
        return 0.0, [], []

    profiles = trend_profiles()
    profile = profiles.get(trend)
    if not profile:
        return 0.0, [], []

    profile = {**profile, "_id": trend}
    per_item = [_garment_trend_score(g, profile) for g in garments]
    if not per_item:
        return 0.0, [], []

    avg = sum(per_item) / len(per_item)
    label = profile.get("label", trend.replace("-", " "))
    highlights: list[str] = []
    warnings: list[str] = []

    if avg >= 0.45:
        highlights.append(f"{label} aesthetic")
    elif avg < 0.0:
        warnings.append(f"not quite {label}")

    return max(-1.0, min(1.0, avg)), highlights, warnings


def available_trends() -> list[dict[str, str]]:
    return [
        {"id": trend_id, "label": profile.get("label", trend_id.replace("-", " ").title())}
        for trend_id, profile in trend_profiles().items()
    ]

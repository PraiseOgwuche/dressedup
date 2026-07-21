"""Outfit Engine v4 Phase 7 — three intentional styling directions.

Each direction is a scoring profile, not a random alternative: a per-garment
affinity in [-1, 1] derived from color restraint, pattern energy, formality,
fabric softness, and footwear character. The outfit-level direction score is
the mean affinity of its pieces and enters FashionMatcher as a weighted
signal only when a direction is requested — the default engine path is
untouched.

Directions (product naming can change later):
  - classic    — restrained colors, solids, versatile smart pieces
  - expressive — stronger color, statement patterns, bolder pieces
  - relaxed    — comfort fabrics, softer structure, casual footwear
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Sequence

from app.fashion.color_harmony import is_neutral_name, normalize_color_name
from app.fashion.knowledge import statement_patterns
from app.taxonomy import FORMALITY_LEVELS

if TYPE_CHECKING:
    from app.models.clothing_item import ClothingItem

DIRECTIONS: tuple[str, ...] = ("classic", "expressive", "relaxed")

DIRECTION_META: dict[str, dict[str, str]] = {
    "classic": {
        "label": "Classic",
        "tagline": "Restrained colors, pieces that go anywhere",
    },
    "expressive": {
        "label": "Expressive",
        "tagline": "Stronger contrast, patterns and statement pieces",
    },
    "relaxed": {
        "label": "Relaxed",
        "tagline": "Comfort first — soft structure, easy footwear",
    },
}

_FORMALITY_INDEX = {level: i for i, level in enumerate(FORMALITY_LEVELS)}

_SOFT_MATERIALS = (
    "cotton", "jersey", "fleece", "knit", "sweat", "terry", "linen", "modal", "corduroy"
)
_STRUCTURED_MATERIALS = ("wool", "tweed", "leather", "silk", "satin", "suit")
_RELAXED_FIT_TOKENS = (
    "oversized", "relaxed", "baggy", "wide", "drawstring", "elastic", "jogger",
    "hoodie", "sweatpant", "sweatshirt", "loose", "slouchy",
)
_CASUAL_FOOTWEAR = ("sneakers", "sandals", "slides", "slip-on", "trainer")
_SHARP_FOOTWEAR = ("loafers", "oxford", "derby", "heels", "brogue", "dress-shoes", "boots")
_STATEMENT_TOKENS = ("graphic", "statement", "bold", "neon", "metallic", "sequin", "print")


def _tokens(item: "ClothingItem") -> str:
    return " ".join(
        (getattr(item, field, None) or "").lower()
        for field in ("subcategory", "name", "product_name", "material")
    )


def _pattern(item: "ClothingItem") -> str:
    return (item.pattern or "solid").lower()


def _formality_idx(item: "ClothingItem") -> Optional[int]:
    return _FORMALITY_INDEX.get(item.formality or "")


def _is_footwear(item: "ClothingItem") -> bool:
    return (item.category or "").lower() in {
        "footwear", "shoes", "sneakers", "heels", "boots", "sandals"
    }


def garment_direction_affinity(item: "ClothingItem", direction: str) -> float:
    """How strongly one garment expresses a direction, in [-1, 1]."""
    color = normalize_color_name(item.color)
    neutral = is_neutral_name(item.color)
    pattern = _pattern(item)
    statement = pattern in statement_patterns()
    tokens = _tokens(item)
    formality = _formality_idx(item)
    footwear = _is_footwear(item)

    score = 0.0
    if direction == "classic":
        score += 0.45 if neutral else -0.30
        score += 0.35 if pattern == "solid" else (-0.45 if statement else -0.10)
        if formality is not None:
            # Peaks at smart-casual; loungewear and full formal both drift away.
            score += 0.30 - abs(formality - _FORMALITY_INDEX.get("smart-casual", 2)) * 0.15
        if footwear and any(t in tokens for t in _SHARP_FOOTWEAR):
            score += 0.25
        if any(t in tokens for t in _RELAXED_FIT_TOKENS):
            score -= 0.20

    elif direction == "expressive":
        score += 0.45 if not neutral else -0.25
        score += 0.50 if statement else (-0.15 if pattern == "solid" else 0.10)
        if any(t in tokens for t in _STATEMENT_TOKENS):
            score += 0.30
        if color in {"red", "orange", "yellow", "pink", "purple", "green"}:
            score += 0.15

    elif direction == "relaxed":
        if formality is not None:
            score += 0.40 - formality * 0.25  # loungewear/casual reward, formal penalty
        if any(t in tokens for t in _SOFT_MATERIALS):
            score += 0.30
        if any(t in tokens for t in _STRUCTURED_MATERIALS):
            score -= 0.30
        if any(t in tokens for t in _RELAXED_FIT_TOKENS):
            score += 0.30
        if footwear:
            if any(t in tokens for t in _CASUAL_FOOTWEAR):
                score += 0.35
            elif any(t in tokens for t in _SHARP_FOOTWEAR):
                score -= 0.35

    return max(-1.0, min(1.0, score))


def score_direction(
    garments: Sequence["ClothingItem"],
    direction: Optional[str],
) -> tuple[float, list[str]]:
    """(raw score in [-1, 1], highlights) for how well the outfit fits the direction."""
    if not direction or direction not in DIRECTIONS or not garments:
        return 0.0, []
    scores = [garment_direction_affinity(g, direction) for g in garments]
    raw = sum(scores) / len(scores)
    highlights: list[str] = []
    if raw > 0.35:
        highlights.append(
            {
                "classic": "a clean, versatile combination",
                "expressive": "pieces that make a statement",
                "relaxed": "an easy, comfortable mix",
            }[direction]
        )
    return raw, highlights

"""Style combination rules — loaded from knowledge.yaml."""

from __future__ import annotations

from itertools import combinations
from typing import TYPE_CHECKING, Any, Optional

from app.fashion.knowledge import (
    archetype_rules,
    category_rules,
    cold_weather_tags,
    footwear_rules,
    occasion_rules,
    pattern_clashes,
    silhouette_rules,
    statement_patterns,
    texture_rules,
    weather_layering_rules,
    weather_season_map,
)
from app.taxonomy import FORMALITY_LEVELS

if TYPE_CHECKING:
    from app.models.clothing_item import ClothingItem

_FORMALITY_INDEX = {level: i for i, level in enumerate(FORMALITY_LEVELS)}


def _formality_index(item: ClothingItem) -> Optional[int]:
    if item.formality in _FORMALITY_INDEX:
        return _FORMALITY_INDEX[item.formality]
    return None


def _pattern_of(item: ClothingItem) -> Optional[str]:
    pattern = (item.pattern or "").lower()
    return pattern if pattern and pattern != "solid" else None


def _footwear_label(item: ClothingItem) -> str:
    return ((item.subcategory or item.category) or "").lower()


def _material_token(item: ClothingItem) -> Optional[str]:
    material = (getattr(item, "material", None) or "").lower()
    if not material:
        return None
    for token in texture_rules().get("material_formality", {}):
        if token in material:
            return token
    return material.split(",")[0].strip().split()[0] if material else None


def _occasion_config(occasion: Optional[str]) -> dict[str, Any]:
    return occasion_rules().get(occasion or "everyday", occasion_rules().get("everyday", {}))


def score_formality(garments: list[ClothingItem], occasion: Optional[str]) -> tuple[float, list[str], list[str]]:
    indexes = [_formality_index(g) for g in garments]
    indexes = [i for i in indexes if i is not None]
    if len(indexes) < 2:
        return 0.0, [], []

    config = _occasion_config(occasion)
    spread = max(indexes) - min(indexes)
    avg = sum(indexes) / len(indexes)
    highlights: list[str] = []
    warnings: list[str] = []

    allowed_gap = int(config.get("formality_gap_max", 2))
    if spread <= allowed_gap:
        score = 0.8 - (spread * 0.15)
        if spread == 0:
            highlights.append(f"consistent {FORMALITY_LEVELS[round(avg)]} level")
        else:
            highlights.append("formality levels align")
    else:
        score = -0.6 - (spread - allowed_gap) * 0.2
        warnings.append("formality mismatch across pieces")

    min_label = config.get("min_formality")
    if min_label and min_label in _FORMALITY_INDEX and min(indexes) < _FORMALITY_INDEX[min_label]:
        score -= 0.5
        warnings.append(f"too casual for {occasion or 'this occasion'}")

    for rule in category_rules():
        incompatible = rule.get("incompatible_formality", [])
        if not incompatible:
            continue
        bad_levels = {_FORMALITY_INDEX[f] for f in incompatible if f in _FORMALITY_INDEX}
        for garment in garments:
            cat = (garment.category or "").lower()
            if cat in rule.get("categories", []) and _formality_index(garment) in bad_levels:
                score -= 0.4
                warnings.append(f"{cat} too formal for this mix")

    return max(-1.0, min(1.0, score)), highlights, warnings


def score_patterns(garments: list[ClothingItem]) -> tuple[float, list[str], list[str]]:
    patterns = [_pattern_of(g) for g in garments]
    patterns = [p for p in patterns if p]
    clashes = pattern_clashes()
    if not patterns:
        return 0.3, [], []

    highlights: list[str] = []
    warnings: list[str] = []

    if len(patterns) == 1:
        highlights.append("one focal pattern balanced with solids")
        return 0.7, highlights, warnings

    score = 0.0
    for a, b in combinations(patterns, 2):
        if frozenset({a, b}) in clashes:
            score -= 0.55
            warnings.append(f"{a} and {b} compete visually")
        else:
            score -= 0.20
    if len(patterns) > 2:
        score -= 0.25
        warnings.append("too many patterns in one outfit")
    return max(-1.0, min(0.5, score)), highlights, warnings


def score_footwear(garments: list[ClothingItem], occasion: Optional[str]) -> tuple[float, list[str], list[str]]:
    shoes = [
        g for g in garments
        if (g.category or "").lower() in {"footwear", "shoes", "sneakers", "boots", "heels", "sandals"}
    ]
    if not shoes:
        return 0.0, [], []

    foot = footwear_rules()
    casual_only = foot["casual_only"]
    formal_types = foot["formal_types"]
    config = _occasion_config(occasion)
    banned = set(config.get("banned_footwear", []))

    shoe = shoes[0]
    label = _footwear_label(shoe)
    formality_idxs = [_formality_index(g) for g in garments if _formality_index(g) is not None]
    if not formality_idxs:
        return 0.0, [], []

    outfit_formality = max(formality_idxs)
    warnings: list[str] = []
    highlights: list[str] = []

    if label in banned or (shoe.subcategory or "").lower() in banned:
        return -0.80, highlights, [f"footwear too casual for {occasion or 'this occasion'}"]

    if outfit_formality >= _FORMALITY_INDEX["business"]:
        if label in casual_only or (shoe.subcategory or "").lower() in casual_only:
            return -0.85, highlights, ["sneakers/sandals with formal pieces"]

    if label in formal_types and outfit_formality <= _FORMALITY_INDEX["smart-casual"]:
        return 0.2, highlights, []

    return 0.5, highlights, []


def score_textures(garments: list[ClothingItem]) -> tuple[float, list[str], list[str]]:
    """Material/texture harmony from knowledge.yaml."""
    materials = [_material_token(g) for g in garments]
    materials = [m for m in materials if m]
    if len(materials) < 2:
        return 0.0, [], []

    rules = texture_rules()
    harmonious = {_pair_set_item(p) for p in rules.get("harmonious", [])}
    clashing = {_pair_set_item(p) for p in rules.get("clashing", [])}

    score = 0.15
    highlights: list[str] = []
    warnings: list[str] = []

    for a, b in combinations(materials, 2):
        pair = frozenset({a, b})
        if pair in clashing:
            score -= 0.50
            warnings.append(f"{a} and {b} textures clash")
        elif pair in harmonious:
            score += 0.35
            highlights.append("complementary textures")

    return max(-1.0, min(1.0, score)), highlights, warnings


def _pair_set_item(pair: list[str]) -> frozenset[str]:
    return frozenset(pair)


def score_season(garments: list[ClothingItem], target_seasons: set[str]) -> tuple[float, list[str]]:
    if not target_seasons:
        return 0.0, []
    hits = misses = 0
    for garment in garments:
        seasons = set(garment.seasons or [])
        if not seasons:
            continue
        if seasons & target_seasons or "all-season" in seasons:
            hits += 1
        else:
            misses += 1
    if hits == 0 and misses == 0:
        return 0.0, []
    score = (hits - misses) / max(hits + misses, 1)
    notes = []
    if score > 0.3:
        notes.append("season-appropriate fabrics")
    return score, notes


def score_occasion_fit(garments: list[ClothingItem], occasion: Optional[str]) -> tuple[float, list[str], list[str]]:
    if not occasion:
        return 0.0, [], []

    warnings: list[str] = []
    highlights: list[str] = []
    config = _occasion_config(occasion)

    if config.get("requires_activewear"):
        non_active = [
            g for g in garments
            if (g.category or "").lower() not in {"activewear"}
            and (g.subcategory or "").lower() not in {"sports-bra", "athletic-top", "athletic-shorts", "tracksuit"}
        ]
        if non_active:
            return -0.8, highlights, ["workout needs athletic pieces"]

    for rule in category_rules():
        blocked = set(rule.get("incompatible_occasions", []))
        if occasion not in blocked:
            continue
        for garment in garments:
            if (garment.category or "").lower() in rule.get("categories", []):
                return -0.7, highlights, [f"{garment.category} not suited for {occasion}"]

    matched = sum(1 for g in garments if not g.occasion or occasion in g.occasion)
    if matched == len(garments) and garments:
        highlights.append(f"suited for {occasion}")
        return 0.6, highlights, warnings
    if matched >= len(garments) // 2:
        return 0.2, highlights, warnings
    return -0.15, highlights, warnings


def weather_seasons(weather_tag: Optional[str]) -> set[str]:
    return weather_season_map().get(weather_tag or "", set())


def needs_outerwear(weather_tag: Optional[str]) -> bool:
    if weather_tag in cold_weather_tags():
        return True
    layer_rule = weather_layering_rules().get(weather_tag or "", {})
    return bool(layer_rule.get("prefer_outerwear"))


def _fit_tokens(item: ClothingItem) -> set[str]:
    tokens: set[str] = set()
    for raw in (
        (item.subcategory or "").lower(),
        (getattr(item, "name", None) or "").lower(),
        (getattr(item, "product_name", None) or "").lower(),
    ):
        for part in raw.replace("-", " ").split():
            if part:
                tokens.add(part)
    return tokens


def score_silhouette(garments: list[ClothingItem]) -> tuple[float, list[str], list[str]]:
    """Proportion balance — e.g. relaxed top + slim bottom."""
    tops = [g for g in garments if (g.category or "").lower() in {"top", "outerwear"}]
    bottoms = [g for g in garments if (g.category or "").lower() == "bottom"]
    if not tops or not bottoms:
        return 0.0, [], []

    top_tokens = set()
    for top in tops:
        top_tokens |= _fit_tokens(top)
    bottom_tokens = set()
    for bottom in bottoms:
        bottom_tokens |= _fit_tokens(bottom)

    highlights: list[str] = []
    warnings: list[str] = []
    best = 0.0
    for rule in silhouette_rules().get("balanced_pairs", []):
        top_fit = set(rule.get("top_fit", []))
        bottom_fit = set(rule.get("bottom_fit", []))
        if top_tokens & top_fit and bottom_tokens & bottom_fit:
            bonus = float(rule.get("bonus", 0.3))
            best = max(best, bonus)
            note = rule.get("note")
            if note:
                highlights.append(note)

    if best == 0.0 and len(tops) > 0 and len(bottoms) > 0:
        # Both oversized can read sloppy unless intentional streetwear.
        oversized_markers = {"oversized", "boxy", "baggy", "wide", "wide-leg", "relaxed"}
        if (top_tokens & oversized_markers) and (bottom_tokens & oversized_markers):
            return -0.15, [], ["double-volume silhouette — try balancing proportions"]

    return max(-1.0, min(1.0, best)), highlights, warnings


def _slot_label(item: ClothingItem) -> str:
    return ((item.subcategory or item.category) or "").lower()


def score_archetype(garments: list[ClothingItem]) -> tuple[float, list[str], list[str]]:
    """Bonus when outfit matches a classic formula from the knowledge base."""
    if len(garments) < 2:
        return 0.0, [], []

    slot_map = {
        "top": [g for g in garments if (g.category or "").lower() in {"top", "outerwear"}],
        "bottom": [g for g in garments if (g.category or "").lower() == "bottom"],
        "footwear": [
            g
            for g in garments
            if (g.category or "").lower() in {"footwear", "shoes", "sneakers", "boots", "heels", "sandals"}
        ],
    }

    best_score = 0.0
    best_name = ""
    for archetype in archetype_rules():
        slots = archetype.get("slots", {})
        if not slots:
            continue
        matches = 0
        checked = 0
        for slot_name, hints in slots.items():
            items = slot_map.get(slot_name, [])
            if not items:
                continue
            checked += 1
            hint_set = {h.lower() for h in hints}
            if any(any(token in _slot_label(item) for token in hint_set) for item in items):
                matches += 1
        if checked >= 2 and matches >= max(2, checked - 1):
            score = float(archetype.get("bonus", 0.35)) * (matches / checked)
            if score > best_score:
                best_score = score
                best_name = archetype.get("name", "classic look")

    highlights = [f"{best_name} formula"] if best_name and best_score > 0 else []
    return max(-1.0, min(1.0, best_score)), highlights, []


def score_weather_materials(
    garments: list[ClothingItem],
    weather_tag: Optional[str],
) -> tuple[float, list[str], list[str]]:
    """Light bonus for weather-appropriate fabrics from knowledge.yaml."""
    if not weather_tag:
        return 0.0, [], []
    rule = weather_layering_rules().get(weather_tag, {})
    if not rule:
        return 0.0, [], []

    prefer = {m.lower() for m in rule.get("prefer_materials", []) + rule.get("bonus_materials", [])}
    if not prefer:
        return 0.0, [], []

    hits = 0
    for garment in garments:
        material = (getattr(garment, "material", None) or "").lower()
        if material and any(token in material for token in prefer):
            hits += 1

    if hits == 0:
        return 0.0, [], []
    ratio = hits / len(garments)
    score = min(0.6, ratio * 0.8)
    return score, ["weather-right fabrics"], []

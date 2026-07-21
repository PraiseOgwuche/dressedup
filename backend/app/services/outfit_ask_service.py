"""Phase 9 — natural-language styling grounded in the real closet.

The parser may interpret occasion, weather, vibe, formality, colors, anchors,
and exclusions — but every outfit is produced by OutfitService from owned
item IDs only. Nothing is invented, and compatibility rules are never bypassed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional, Sequence

from sqlalchemy.orm import Session

from app.fashion.color_harmony import normalize_color_name
from app.fashion.direction_profiles import DIRECTIONS
from app.fashion.trend_rules import available_trends
from app.models.clothing_item import ClothingItem
from app.services.outfit_service import OutfitService
from app.taxonomy import FORMALITY_LEVELS, OCCASIONS, WEATHER_TAGS

# Longer phrases first so "formal event" wins over "formal".
_OCCASION_PHRASES: list[tuple[str, str]] = [
    ("formal event", "formal-event"),
    ("night out", "party"),
    ("date night", "date"),
    ("smart casual", "work"),
    ("business casual", "work"),
    ("business-casual", "work"),
    ("job interview", "work"),
    ("office", "work"),
    ("work", "work"),
    ("gym", "workout"),
    ("workout", "workout"),
    ("exercise", "workout"),
    ("running", "workout"),
    ("dinner date", "date"),
    ("dinner", "date"),
    ("first date", "date"),
    ("date", "date"),
    ("party", "party"),
    ("club", "party"),
    ("wedding", "formal-event"),
    ("gala", "formal-event"),
    ("black tie", "formal-event"),
    ("formal", "formal-event"),
    ("vacation", "travel"),
    ("flying", "travel"),
    ("flight", "travel"),
    ("travel", "travel"),
    ("hike", "outdoor"),
    ("hiking", "outdoor"),
    ("camping", "outdoor"),
    ("outdoor", "outdoor"),
    ("lounge", "loungewear"),
    ("loungewear", "loungewear"),
    ("chill", "loungewear"),
    ("relax", "loungewear"),
    ("everyday", "everyday"),
    ("errands", "everyday"),
]

_WEATHER_PHRASES: list[tuple[str, str]] = [
    ("snowing", "snow"),
    ("snowy", "snow"),
    ("snow", "snow"),
    ("raining", "rainy"),
    ("rainy", "rainy"),
    ("rain", "rainy"),
    ("freezing cold", "cold"),
    ("freezing", "cold"),
    ("chilly", "cold"),
    ("cold", "cold"),
    ("mild", "mild"),
    ("warm", "warm"),
    ("humid", "hot"),
    ("hot", "hot"),
]

_TREND_PHRASES: list[tuple[str, str]] = [
    ("quiet luxury", "quiet-luxury"),
    ("old money", "quiet-luxury"),
    ("street wear", "streetwear"),
    ("streetwear", "streetwear"),
    ("street style", "streetwear"),
    ("minimalist", "minimalist"),
    ("minimal", "minimalist"),
    ("preppy", "preppy"),
    ("ivy league", "preppy"),
    ("timeless", "classic"),
]

_FORMALITY_PHRASES: list[tuple[str, str]] = [
    ("black tie", "formal"),
    ("business casual", "smart-casual"),
    ("business-casual", "smart-casual"),
    ("smart casual", "smart-casual"),
    ("smart-casual", "smart-casual"),
    ("loungewear", "loungewear"),
    ("formal", "formal"),
    ("business", "business"),
    ("casual", "casual"),
]

_DIRECTION_PHRASES: list[tuple[str, str]] = [
    ("expressive", "expressive"),
    ("statement", "expressive"),
    ("bold", "expressive"),
    ("classic", "classic"),
    ("polished", "classic"),
    ("relaxed", "relaxed"),
    ("comfy", "relaxed"),
    ("comfortable", "relaxed"),
    ("easygoing", "relaxed"),
]

# (phrase, slot hint, subcategory/category tokens to match)
_GARMENT_PHRASES: list[tuple[str, str, tuple[str, ...]]] = [
    ("navy trousers", "bottom", ("trousers", "pants", "chinos")),
    ("trousers", "bottom", ("trousers", "pants", "chinos")),
    ("pants", "bottom", ("trousers", "pants", "chinos")),
    ("jeans", "bottom", ("jeans",)),
    ("shorts", "bottom", ("shorts",)),
    ("skirt", "bottom", ("skirt",)),
    ("blazer", "outerwear", ("blazer",)),
    ("jacket", "outerwear", ("jacket", "blazer", "coat")),
    ("coat", "outerwear", ("coat", "parka")),
    ("hoodie", "outerwear", ("hoodie",)),
    ("sneakers", "shoes", ("sneakers", "trainer")),
    ("trainers", "shoes", ("sneakers", "trainer")),
    ("loafers", "shoes", ("loafers",)),
    ("boots", "shoes", ("boots",)),
    ("heels", "shoes", ("heels",)),
    ("sandals", "shoes", ("sandals",)),
    ("dress", "dress", ("dress", "midi", "maxi", "mini")),
    ("jumpsuit", "dress", ("jumpsuit",)),
    ("shirt", "top", ("shirt", "blouse")),
    ("tee", "top", ("t-shirt", "tee")),
    ("t-shirt", "top", ("t-shirt", "tee")),
    ("sweater", "top", ("sweater",)),
    ("hoodie", "top", ("hoodie",)),
]

_COLOR_TOKENS = (
    "black", "white", "navy", "blue", "red", "green", "grey", "gray", "beige",
    "brown", "tan", "olive", "cream", "pink", "purple", "orange", "yellow",
    "charcoal", "khaki", "rust", "burgundy", "maroon", "denim",
)

_EXCLUDE_PATTERNS = (
    r"\bnot\s+([a-z][\w-]*)",
    r"\bno\s+([a-z][\w-]*)",
    r"\bwithout\s+([a-z][\w-]*)",
    r"\bexcept\s+([a-z][\w-]*)",
    r"\bbut\s+not\s+([a-z][\w-]*)",
)

_FRESHNESS_PATTERNS = (
    r"haven'?t\s+worn",
    r"have\s+not\s+worn",
    r"least[- ]worn",
    r"rarely\s+worn",
    r"not\s+worn\s+recently",
    r"been\s+sitting",
)

_ANCHOR_CUES = (
    r"centered\s+on",
    r"built\s+around",
    r"around\s+my",
    r"with\s+my",
    r"using\s+my",
    r"use\s+(?:the|my)",
    r"feature\s+my",
    r"include\s+my",
)


@dataclass
class ParsedOutfitIntent:
    occasion: Optional[str] = None
    weather_tag: Optional[str] = None
    trend: Optional[str] = None
    formality: Optional[str] = None
    direction: Optional[str] = None
    preferred_colors: list[str] = field(default_factory=list)
    excluded_tokens: list[str] = field(default_factory=list)
    anchor_item_id: Optional[int] = None
    anchor_label: Optional[str] = None
    exclude_item_ids: list[int] = field(default_factory=list)
    freshness_slot: Optional[str] = None
    interpretation: str = ""

    def to_dict(self) -> dict:
        return {
            "occasion": self.occasion,
            "weather_tag": self.weather_tag,
            "trend": self.trend,
            "formality": self.formality,
            "direction": self.direction,
            "preferred_colors": self.preferred_colors,
            "excluded_tokens": self.excluded_tokens,
            "anchor_item_id": self.anchor_item_id,
            "anchor_label": self.anchor_label,
            "exclude_item_ids": self.exclude_item_ids,
            "freshness_slot": self.freshness_slot,
            "interpretation": self.interpretation,
        }


def _match_phrase(text: str, phrases: list[tuple[str, str]]) -> Optional[str]:
    for phrase, value in phrases:
        if phrase in text:
            return value
    return None


def _match_token(text: str, vocabulary: list[str]) -> Optional[str]:
    tokens = set(re.findall(r"[a-z]+(?:-[a-z]+)?", text))
    for item in sorted(vocabulary, key=len, reverse=True):
        if item in tokens:
            return item
    return None


def _match_trend(text: str) -> Optional[str]:
    trend = _match_phrase(text, _TREND_PHRASES)
    if trend:
        return trend
    # "classic" as vibe maps to direction first; trend classic only if explicit.
    if "classic vibe" in text or "classic look" in text:
        return "classic"
    known = {t["id"] for t in available_trends()}
    return _match_token(text, sorted(known, key=len, reverse=True))


def _extract_colors(text: str) -> list[str]:
    found: list[str] = []
    for color in _COLOR_TOKENS:
        if re.search(rf"\b{re.escape(color)}\b", text):
            found.append(normalize_color_name(color))
    return found


def _extract_exclusions(text: str) -> list[str]:
    tokens: list[str] = []
    for pattern in _EXCLUDE_PATTERNS:
        for match in re.finditer(pattern, text):
            token = match.group(1).lower()
            if token in {"a", "an", "the", "my", "any", "too"}:
                continue
            tokens.append(token)
    # Dedupe, preserve order.
    seen: set[str] = set()
    out: list[str] = []
    for t in tokens:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def _wants_freshness(text: str) -> bool:
    return any(re.search(p, text) for p in _FRESHNESS_PATTERNS)


def _has_anchor_cue(text: str) -> bool:
    return any(re.search(p, text) for p in _ANCHOR_CUES)


def _item_text(item: ClothingItem) -> str:
    return " ".join(
        filter(
            None,
            [
                (item.name or "").lower(),
                (item.product_name or "").lower(),
                (item.category or "").lower(),
                (item.subcategory or "").lower(),
                normalize_color_name(item.color),
                (item.brand or "").lower(),
            ],
        )
    )


def _item_matches_tokens(item: ClothingItem, tokens: Sequence[str]) -> bool:
    blob = _item_text(item)
    return any(tok in blob for tok in tokens)


def _score_anchor_candidate(item: ClothingItem, color: Optional[str], tokens: Sequence[str]) -> float:
    blob = _item_text(item)
    score = 0.0
    if color and color in normalize_color_name(item.color):
        score += 3.0
    elif color and color in blob:
        score += 1.5
    for tok in tokens:
        if tok in (item.subcategory or "").lower():
            score += 2.0
        elif tok in (item.category or "").lower():
            score += 1.5
        elif tok in blob:
            score += 1.0
    # Prefer cleaner, less-worn when tying.
    score -= 0.01 * (item.times_worn or 0)
    return score


def _resolve_anchor(
    text: str,
    closet: Sequence[ClothingItem],
    colors: list[str],
) -> tuple[Optional[ClothingItem], Optional[str]]:
    """Map a garment mention onto a real closet item, or None."""
    if not closet:
        return None, None

    # Prefer explicit anchor cues; still try if a clear garment phrase exists.
    mentioned = [
        (phrase, slot, tokens)
        for phrase, slot, tokens in _GARMENT_PHRASES
        if phrase in text
    ]
    if not mentioned:
        return None, None
    if not _has_anchor_cue(text) and not any(c in text for c in colors):
        # Bare "jeans" in "not jeans" shouldn't lock an anchor.
        if any(re.search(rf"(?:not|no|without|except)\s+{re.escape(p)}", text) for p, _, _ in mentioned):
            return None, None

    phrase, slot, tokens = mentioned[0]
    color: Optional[str] = None
    window_start = max(0, text.find(phrase) - 24)
    window_end = text.find(phrase) + len(phrase) + 24
    window = text[window_start:window_end]
    for c in colors:
        if c in window:
            color = c
            break

    candidates = [
        item
        for item in closet
        if item.is_clean
        and (OutfitService.slot_for_item(item) == slot or _item_matches_tokens(item, tokens))
    ]
    if not candidates:
        candidates = [item for item in closet if item.is_clean and _item_matches_tokens(item, tokens)]
    if not candidates:
        return None, None

    ranked = sorted(
        candidates,
        key=lambda item: _score_anchor_candidate(item, color, tokens),
        reverse=True,
    )
    best = ranked[0]
    if _score_anchor_candidate(best, color, tokens) <= 0:
        return None, None
    label = best.name or phrase
    return best, label


def _resolve_exclusions(
    closet: Sequence[ClothingItem],
    excluded_tokens: Sequence[str],
) -> list[int]:
    if not excluded_tokens:
        return []
    ids: list[int] = []
    for item in closet:
        blob = _item_text(item)
        for token in excluded_tokens:
            if token in blob or token == normalize_color_name(item.color):
                ids.append(item.id)
                break
            # "sneakers" should match category sneakers / subcategory
            if token in (item.category or "").lower() or token in (item.subcategory or "").lower():
                ids.append(item.id)
                break
    return ids


def _resolve_freshness_anchor(
    closet: Sequence[ClothingItem],
    text: str,
    exclude_ids: set[int],
) -> tuple[Optional[ClothingItem], Optional[str]]:
    """'Use the jacket I haven't worn recently' → least-worn matching piece."""
    slot = None
    for phrase, hinted_slot, _ in _GARMENT_PHRASES:
        if phrase in text:
            slot = hinted_slot
            break
    if slot is None:
        if "jacket" in text or "coat" in text or "blazer" in text:
            slot = "outerwear"
        elif "shoe" in text or "sneaker" in text:
            slot = "shoes"
        else:
            return None, None

    pool = [
        item
        for item in closet
        if item.is_clean
        and item.id not in exclude_ids
        and OutfitService.slot_for_item(item) == slot
    ]
    if not pool:
        return None, None
    pick = min(pool, key=lambda i: (i.times_worn or 0, i.id))
    return pick, pick.name


def _build_interpretation(intent: "ParsedOutfitIntent") -> str:
    parts: list[str] = []
    if intent.anchor_label:
        parts.append(f"built around {intent.anchor_label}")
    if intent.occasion:
        parts.append(intent.occasion.replace("-", " "))
    if intent.weather_tag:
        parts.append(f"{intent.weather_tag} weather")
    if intent.formality:
        parts.append(intent.formality.replace("-", " "))
    if intent.direction:
        parts.append(intent.direction)
    if intent.trend:
        label = next(
            (t["label"] for t in available_trends() if t["id"] == intent.trend),
            intent.trend.replace("-", " "),
        )
        parts.append(label)
    if intent.preferred_colors and not intent.anchor_label:
        parts.append(f"favoring {'/'.join(intent.preferred_colors)}")
    if intent.excluded_tokens:
        parts.append(f"avoiding {'/'.join(intent.excluded_tokens)}")
    if intent.freshness_slot:
        parts.append(f"reaching for a less-worn {intent.freshness_slot}")

    if parts:
        return f"Dressing for {' · '.join(parts)}"
    return "General outfit from your closet"


def parse_outfit_query(
    query: str,
    closet: Sequence[ClothingItem] | None = None,
) -> ParsedOutfitIntent:
    """Extract structured intent. When closet is provided, resolve real item IDs."""
    text = " ".join(query.lower().strip().split())
    if not text:
        return ParsedOutfitIntent(interpretation="Tell me what you're dressing for.")

    closet = list(closet or [])
    colors = _extract_colors(text)
    excluded_tokens = _extract_exclusions(text)

    occasion = _match_phrase(text, _OCCASION_PHRASES) or _match_token(text, OCCASIONS)
    weather_tag = _match_phrase(text, _WEATHER_PHRASES) or _match_token(text, WEATHER_TAGS)
    formality = _match_phrase(text, _FORMALITY_PHRASES) or _match_token(text, FORMALITY_LEVELS)
    direction = _match_phrase(text, _DIRECTION_PHRASES)
    if direction and direction not in DIRECTIONS:
        direction = None
    trend = _match_trend(text)
    # Direction "classic" wins over trend when the user said relaxed/expressive/classic as a mood.
    if direction == "classic" and trend == "classic":
        pass
    elif direction and trend == direction:
        trend = None

    # Formality can imply occasion when none was stated.
    if formality in {"business", "smart-casual"} and not occasion:
        occasion = "work"
    if formality == "formal" and not occasion:
        occasion = "formal-event"
    if formality == "loungewear" and not occasion:
        occasion = "loungewear"

    exclude_item_ids = _resolve_exclusions(closet, excluded_tokens)
    exclude_set = set(exclude_item_ids)

    anchor: Optional[ClothingItem] = None
    anchor_label: Optional[str] = None
    freshness_slot: Optional[str] = None

    if _wants_freshness(text):
        anchor, anchor_label = _resolve_freshness_anchor(closet, text, exclude_set)
        if anchor is not None:
            freshness_slot = OutfitService.slot_for_item(anchor)

    if anchor is None:
        anchor, anchor_label = _resolve_anchor(text, closet, colors)

    # Preferred colors that aren't just describing the locked anchor.
    preferred_colors = list(colors)
    if anchor is not None and anchor.color:
        anchor_color = normalize_color_name(anchor.color)
        preferred_colors = [c for c in preferred_colors if c != anchor_color]

    intent = ParsedOutfitIntent(
        occasion=occasion,
        weather_tag=weather_tag,
        trend=trend,
        formality=formality,
        direction=direction,
        preferred_colors=preferred_colors,
        excluded_tokens=excluded_tokens,
        anchor_item_id=anchor.id if anchor else None,
        anchor_label=anchor_label,
        exclude_item_ids=exclude_item_ids,
        freshness_slot=freshness_slot,
    )
    intent.interpretation = _build_interpretation(intent)
    return intent


def _suggestion_item_ids(payload: dict) -> set[int]:
    ids: set[int] = set()
    for slot in ("dress", "top", "bottom", "shoes", "outerwear", "bag", "accessory", "headwear"):
        piece = payload.get(slot)
        if piece is not None and getattr(piece, "id", None) is not None:
            ids.add(piece.id)
    for alt in payload.get("alternatives") or []:
        if getattr(alt, "id", None) is not None:
            ids.add(alt.id)
    return ids


def _assert_grounded(payload: dict, closet_ids: set[int]) -> None:
    """Hard guarantee: every selected piece is an owned closet ID."""
    leaked = _suggestion_item_ids(payload) - closet_ids
    if leaked:
        raise RuntimeError(f"Ask path proposed non-closet item ids: {sorted(leaked)}")


def fulfill_outfit_ask(db: Session, user_id: int, query: str) -> dict:
    """Parse → deterministic engine → grounded suggestion. Never invents items."""
    closet = (
        db.query(ClothingItem)
        .filter(ClothingItem.user_id == user_id)
        .all()
    )
    closet_ids = {item.id for item in closet}
    intent = parse_outfit_query(query, closet)
    exclude_ids = set(intent.exclude_item_ids)

    if intent.anchor_item_id is not None:
        suggestion = _suggest_around_with_excludes(db, user_id, intent, exclude_ids)
    else:
        suggestion = OutfitService.get_suggestion(
            db=db,
            user_id=user_id,
            weather_tag=intent.weather_tag,
            occasion=intent.occasion,
            include_alternative=True,
            exclude_ids=exclude_ids or None,
            trend=intent.trend,
            direction=intent.direction,
        )
        if intent.preferred_colors and suggestion:
            suggestion = _maybe_prefer_colors(
                db, user_id, intent, suggestion, closet, exclude_ids
            )

    if suggestion:
        _assert_grounded(suggestion, closet_ids)

    return {
        "query": query.strip(),
        "parsed": intent,
        "suggestion": suggestion,
    }


def _suggest_around_with_excludes(
    db: Session,
    user_id: int,
    intent: ParsedOutfitIntent,
    exclude_ids: set[int],
) -> dict:
    """Lock a real closet anchor; engine never sees excluded items as candidates."""
    suggestion = OutfitService.suggest_around_item(
        db,
        user_id,
        intent.anchor_item_id,
        weather_tag=intent.weather_tag,
        occasion=intent.occasion,
        exclude_ids=exclude_ids - {intent.anchor_item_id},
        direction=intent.direction,
        trend=intent.trend,
    )
    if not suggestion:
        return OutfitService.get_suggestion(
            db=db,
            user_id=user_id,
            weather_tag=intent.weather_tag,
            occasion=intent.occasion,
            include_alternative=True,
            exclude_ids=exclude_ids or None,
            trend=intent.trend,
            direction=intent.direction,
        )
    return suggestion


def _maybe_prefer_colors(
    db: Session,
    user_id: int,
    intent: ParsedOutfitIntent,
    suggestion: dict,
    closet: Sequence[ClothingItem],
    exclude_ids: set[int],
) -> dict:
    preferred = {normalize_color_name(c) for c in intent.preferred_colors}
    if not preferred:
        return suggestion

    def has_preferred(piece) -> bool:
        if piece is None:
            return False
        return normalize_color_name(piece.color) in preferred

    already = any(
        has_preferred(suggestion.get(slot))
        for slot in ("dress", "top", "bottom", "shoes", "outerwear")
    )
    if already:
        return suggestion

    color_matches = [
        item
        for item in closet
        if item.is_clean
        and item.id not in exclude_ids
        and normalize_color_name(item.color) in preferred
    ]
    if not color_matches:
        return suggestion

    match_slots = {OutfitService.slot_for_item(i) for i in color_matches if OutfitService.slot_for_item(i)}
    nudge_exclude = set(exclude_ids)
    for item in closet:
        slot = OutfitService.slot_for_item(item)
        if slot in match_slots and normalize_color_name(item.color) not in preferred:
            nudge_exclude.add(item.id)

    nudged = OutfitService.get_suggestion(
        db=db,
        user_id=user_id,
        weather_tag=intent.weather_tag,
        occasion=intent.occasion,
        include_alternative=True,
        exclude_ids=nudge_exclude,
        trend=intent.trend,
        direction=intent.direction,
    )
    return nudged or suggestion

"""Parse natural-language outfit requests into structured outfit-engine context."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from app.fashion.trend_rules import available_trends
from app.taxonomy import OCCASIONS, WEATHER_TAGS

# Longer phrases first so "formal event" wins over "formal".
_OCCASION_PHRASES: list[tuple[str, str]] = [
    ("formal event", "formal-event"),
    ("night out", "party"),
    ("date night", "date"),
    ("smart casual", "work"),
    ("business casual", "work"),
    ("job interview", "work"),
    ("office", "work"),
    ("work", "work"),
    ("gym", "workout"),
    ("workout", "workout"),
    ("exercise", "workout"),
    ("running", "workout"),
    ("dinner date", "date"),
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
    ("casual", "everyday"),
    ("errands", "everyday"),
]

_WEATHER_PHRASES: list[tuple[str, str]] = [
    ("snowing", "snow"),
    ("snowy", "snow"),
    ("snow", "snow"),
    ("raining", "rainy"),
    ("rainy", "rainy"),
    ("rain", "rainy"),
    ("freezing", "cold"),
    ("freezing cold", "cold"),
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
    ("classic", "classic"),
    ("timeless", "classic"),
]


@dataclass
class ParsedOutfitIntent:
    occasion: Optional[str] = None
    weather_tag: Optional[str] = None
    trend: Optional[str] = None
    interpretation: str = ""

    def to_dict(self) -> dict:
        return {
            "occasion": self.occasion,
            "weather_tag": self.weather_tag,
            "trend": self.trend,
            "interpretation": self.interpretation,
        }


def _match_phrase(text: str, phrases: list[tuple[str, str]]) -> Optional[str]:
    for phrase, value in phrases:
        if phrase in text:
            return value
    return None


def _match_token(text: str, vocabulary: list[str]) -> Optional[str]:
    tokens = set(re.findall(r"[a-z]+(?:-[a-z]+)?", text))
    for item in vocabulary:
        if item in tokens:
            return item
    return None


def _match_trend(text: str) -> Optional[str]:
    trend = _match_phrase(text, _TREND_PHRASES)
    if trend:
        return trend
    known = {t["id"] for t in available_trends()}
    return _match_token(text, sorted(known, key=len, reverse=True))


def parse_outfit_query(query: str) -> ParsedOutfitIntent:
    """Extract occasion, weather, and vibe from free text."""
    text = " ".join(query.lower().strip().split())
    if not text:
        return ParsedOutfitIntent(interpretation="Tell me what you're dressing for.")

    occasion = _match_phrase(text, _OCCASION_PHRASES) or _match_token(text, OCCASIONS)
    weather_tag = _match_phrase(text, _WEATHER_PHRASES) or _match_token(text, WEATHER_TAGS)
    trend = _match_trend(text)

    parts: list[str] = []
    if occasion:
        parts.append(occasion.replace("-", " "))
    if weather_tag:
        parts.append(f"{weather_tag} weather")
    if trend:
        label = next(
            (t["label"] for t in available_trends() if t["id"] == trend),
            trend.replace("-", " "),
        )
        parts.append(label)

    if parts:
        interpretation = f"Dressing for {' · '.join(parts)}"
    else:
        interpretation = "General outfit from your closet"

    return ParsedOutfitIntent(
        occasion=occasion,
        weather_tag=weather_tag,
        trend=trend,
        interpretation=interpretation,
    )

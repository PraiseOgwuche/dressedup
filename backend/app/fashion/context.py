"""Outfit matching context passed through the fashion engine."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MatchContext:
    """Weather, occasion, and target seasons for a single outfit suggestion."""

    weather_tag: Optional[str] = None
    occasion: Optional[str] = None
    target_seasons: set[str] = field(default_factory=set)

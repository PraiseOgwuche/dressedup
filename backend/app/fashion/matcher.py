"""Unified outfit scoring — fashion knowledge + optional personalization."""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
from typing import TYPE_CHECKING, Optional

from app.fashion.color_harmony import outfit_color_score
from app.fashion.context import MatchContext
from app.fashion.style_rules import (
    needs_outerwear,
    score_footwear,
    score_formality,
    score_occasion_fit,
    score_patterns,
    score_season,
    score_textures,
)
from app.fashion.trend_rules import score_occasion_palette, score_trend_fit

if TYPE_CHECKING:
    from app.models.clothing_item import ClothingItem

# Layer 1 weights (fashion standards). Sum of absolute weights ~= 1.0 scale target.
_W_COLOR = 0.26
_W_FORMALITY = 0.18
_W_PATTERN = 0.10
_W_TEXTURE = 0.07
_W_FOOTWEAR = 0.10
_W_SEASON = 0.08
_W_OCCASION = 0.05
_W_PALETTE = 0.08
_W_TREND = 0.08
_W_FRESH = 0.02

# Layer 2 — learned preferences can move the needle but not override hard clashes.
_W_PERSONAL = 0.35


@dataclass
class ScoreBreakdown:
    total: float = 0.0
    color: float = 0.0
    formality: float = 0.0
    pattern: float = 0.0
    texture: float = 0.0
    footwear: float = 0.0
    season: float = 0.0
    occasion: float = 0.0
    occasion_palette: float = 0.0
    trend: float = 0.0
    freshness: float = 0.0
    personalization: float = 0.0
    highlights: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def rationale(self) -> Optional[str]:
        if not self.highlights and not self.warnings:
            return "Built from your freshest clean pieces."
        parts: list[str] = []
        if self.highlights:
            parts.append(self._join(self.highlights[:3]))
        if self.warnings:
            parts.append("watch: " + self._join(self.warnings[:2]))
        if self.personalization > 0.15:
            parts.append("matches your past favorites")
        return "Picked because " + "; ".join(parts) + "."

    @staticmethod
    def _join(items: list[str]) -> str:
        if len(items) == 1:
            return items[0]
        return ", ".join(items[:-1]) + " and " + items[-1]


class FashionMatcher:
    @classmethod
    def score_outfit(
        cls,
        garments: list[ClothingItem],
        context: MatchContext,
        personalization: float = 0.0,
        personal_notes: Optional[list[str]] = None,
    ) -> ScoreBreakdown:
        garments = [g for g in garments if g is not None]
        breakdown = ScoreBreakdown(personalization=personalization)

        if not garments:
            return breakdown

        pairs = [
            (a.color_hex, a.color, b.color_hex, b.color)
            for a, b in combinations(garments, 2)
        ]
        color_raw, color_notes = outfit_color_score(pairs)
        breakdown.color = color_raw
        breakdown.highlights.extend(color_notes)

        form_raw, form_hi, form_warn = score_formality(garments, context.occasion)
        breakdown.formality = form_raw
        breakdown.highlights.extend(form_hi)
        breakdown.warnings.extend(form_warn)

        pat_raw, pat_hi, pat_warn = score_patterns(garments)
        breakdown.pattern = pat_raw
        breakdown.highlights.extend(pat_hi)
        breakdown.warnings.extend(pat_warn)

        tex_raw, tex_hi, tex_warn = score_textures(garments)
        breakdown.texture = tex_raw
        breakdown.highlights.extend(tex_hi)
        breakdown.warnings.extend(tex_warn)

        foot_raw, foot_hi, foot_warn = score_footwear(garments, context.occasion)
        breakdown.footwear = foot_raw
        breakdown.highlights.extend(foot_hi)
        breakdown.warnings.extend(foot_warn)

        season_raw, season_notes = score_season(garments, context.target_seasons)
        breakdown.season = season_raw
        breakdown.highlights.extend(season_notes)

        occ_raw, occ_hi, occ_warn = score_occasion_fit(garments, context.occasion)
        breakdown.occasion = occ_raw
        breakdown.highlights.extend(occ_hi)
        breakdown.warnings.extend(occ_warn)

        pal_raw, pal_hi, pal_warn = score_occasion_palette(garments, context.occasion)
        breakdown.occasion_palette = pal_raw
        breakdown.highlights.extend(pal_hi)
        breakdown.warnings.extend(pal_warn)

        trend_raw, trend_hi, trend_warn = score_trend_fit(garments, context.trend)
        breakdown.trend = trend_raw
        breakdown.highlights.extend(trend_hi)
        breakdown.warnings.extend(trend_warn)

        wears = sum((g.times_worn or 0) for g in garments)
        breakdown.freshness = -min(wears * 0.02, 0.25)

        if personal_notes:
            breakdown.highlights.extend(personal_notes)

        breakdown.total = (
            _W_COLOR * breakdown.color
            + _W_FORMALITY * breakdown.formality
            + _W_PATTERN * breakdown.pattern
            + _W_TEXTURE * breakdown.texture
            + _W_FOOTWEAR * breakdown.footwear
            + _W_SEASON * breakdown.season
            + _W_OCCASION * breakdown.occasion
            + _W_PALETTE * breakdown.occasion_palette
            + _W_TREND * breakdown.trend
            + _W_FRESH * breakdown.freshness
            + _W_PERSONAL * personalization
        )
        return breakdown

    @classmethod
    def outerwear_needed(cls, weather_tag: Optional[str]) -> bool:
        return needs_outerwear(weather_tag)

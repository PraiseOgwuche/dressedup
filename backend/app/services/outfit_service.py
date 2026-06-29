"""Outfit suggestion engine.

Picks a cohesive top / bottom / shoes (+ optional outerwear) by scoring candidate
combinations on color harmony, formality coherence, season fit, and pattern balance,
with a freshness nudge toward less-worn items. Every signal degrades gracefully: when
items lack an attribute, that signal contributes 0, so a closet of attribute-less items
falls back to the old "least-worn per slot" behavior.
"""

import colorsys
import random
from itertools import combinations
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.clothing_item import ClothingItem
from app.taxonomy import FORMALITY_LEVELS

# Ordinal position of each formality level (loungewear=0 ... formal=4).
_FORMALITY_INDEX = {level: i for i, level in enumerate(FORMALITY_LEVELS)}

# Color names treated as neutral (pair with anything) when no hex is available.
_NEUTRAL_NAMES = {
    "black", "white", "gray", "grey", "beige", "tan", "khaki", "cream",
    "navy", "charcoal", "ivory", "nude", "brown", "denim",
}

# Coarse weather bucket -> seasons it implies, used to reward season-appropriate items.
_WEATHER_SEASONS = {
    "hot": {"summer"},
    "warm": {"summer", "spring"},
    "mild": {"spring", "fall"},
    "cold": {"winter", "fall"},
    "rainy": {"fall", "spring"},
    "snow": {"winter"},
}
_COLD_WEATHER = {"cold", "snow", "rainy"}

# Scoring weights. Color cohesion dominates; freshness only breaks near-ties.
_W_COLOR = 1.0
_W_FORMALITY = 0.4
_W_SEASON = 0.5
_W_PATTERN = 0.6
_W_FRESH = 0.03

# Bound combinatorial search; a personal closet rarely needs more per slot.
_SLOT_CAP = 10

# Combinations within this score of the best are treated as equally good, so a fresh
# "Generate" picks among them at random for variety instead of always the same outfit.
_VARIETY_MARGIN = 0.75


class OutfitService:
    TOP_CATEGORIES = {"top", "shirt", "t-shirt", "blouse", "sweater"}
    BOTTOM_CATEGORIES = {"bottom", "pants", "jeans", "shorts", "skirt"}
    SHOE_CATEGORIES = {"shoes", "sneakers", "heels", "boots", "sandals", "footwear"}
    OUTERWEAR_CATEGORIES = {"jacket", "coat", "hoodie", "outerwear"}

    # Activewear is its own category; route its pieces to top/bottom slots by subcategory
    # so workout outfits can be assembled.
    TOP_SUBCATEGORIES = {"sports-bra", "athletic-top", "tracksuit"}
    BOTTOM_SUBCATEGORIES = {"athletic-shorts"}

    # ----- attribute helpers -------------------------------------------------

    @staticmethod
    def _hsv(hex_color: Optional[str]) -> Optional[tuple]:
        if not hex_color:
            return None
        value = hex_color.strip().lstrip("#")
        if len(value) != 6:
            return None
        try:
            r, g, b = (int(value[i : i + 2], 16) / 255.0 for i in (0, 2, 4))
        except ValueError:
            return None
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        return h * 360.0, s, v

    @staticmethod
    def _is_neutral(hsv: tuple) -> bool:
        _, s, v = hsv
        return s < 0.20 or v < 0.18

    @staticmethod
    def _hue_distance(h1: float, h2: float) -> float:
        d = abs(h1 - h2) % 360.0
        return min(d, 360.0 - d)

    @classmethod
    def _pair_color_score(cls, a: ClothingItem, b: ClothingItem) -> float:
        hsv_a, hsv_b = cls._hsv(a.color_hex), cls._hsv(b.color_hex)
        if hsv_a and hsv_b:
            if cls._is_neutral(hsv_a) or cls._is_neutral(hsv_b):
                return 0.6
            dh = cls._hue_distance(hsv_a[0], hsv_b[0])
            if dh <= 25:
                return 0.8  # monochrome / analogous
            if dh >= 150:
                return 0.7  # complementary
            if dh < 60:
                return 0.3  # loosely analogous
            return -0.4  # clashing mid-distance hues
        # Fallback to color names.
        name_a = (a.color or "").lower()
        name_b = (b.color or "").lower()
        if not name_a or not name_b:
            return 0.0
        if name_a in _NEUTRAL_NAMES or name_b in _NEUTRAL_NAMES:
            return 0.3
        if name_a == name_b:
            return 0.4
        return 0.0

    @classmethod
    def _score_outfit(cls, garments: List[ClothingItem], target_seasons: set) -> float:
        garments = [g for g in garments if g is not None]
        if not garments:
            return 0.0
        score = 0.0

        for a, b in combinations(garments, 2):
            score += _W_COLOR * cls._pair_color_score(a, b)

        formality_idxs = [
            _FORMALITY_INDEX[g.formality] for g in garments if g.formality in _FORMALITY_INDEX
        ]
        if len(formality_idxs) >= 2:
            score -= _W_FORMALITY * (max(formality_idxs) - min(formality_idxs))

        if target_seasons:
            for g in garments:
                seasons = set(g.seasons or [])
                if not seasons:
                    continue
                if seasons & target_seasons or "all-season" in seasons:
                    score += _W_SEASON
                else:
                    score -= _W_SEASON

        statement = [g for g in garments if g.pattern and g.pattern != "solid"]
        if len(statement) >= 2:
            score -= _W_PATTERN * (len(statement) - 1)

        score -= _W_FRESH * sum((g.times_worn or 0) for g in garments)
        return score

    # ----- candidate selection ----------------------------------------------

    @staticmethod
    def _candidates(
        items: List[ClothingItem],
        category_set: set,
        weather_tag: Optional[str],
        occasion: Optional[str],
        exclude_ids: Optional[set] = None,
        subcategory_set: Optional[set] = None,
    ) -> List[ClothingItem]:
        exclude_ids = exclude_ids or set()
        subcategory_set = subcategory_set or set()
        pool = [
            i
            for i in items
            if i.id not in exclude_ids
            and i.is_clean
            and (
                i.category.lower() in category_set
                or (i.subcategory or "").lower() in subcategory_set
            )
        ]
        if weather_tag:
            matched = [i for i in pool if not i.weather_tag or weather_tag in i.weather_tag]
            if matched:
                pool = matched
        if occasion:
            matched = [i for i in pool if not i.occasion or occasion in i.occasion]
            if matched:
                pool = matched
        pool.sort(key=lambda x: x.times_worn or 0)
        return pool[:_SLOT_CAP]

    # ----- main entry point --------------------------------------------------

    @classmethod
    def get_suggestion(
        cls,
        db: Session,
        user_id: int,
        weather_tag: Optional[str],
        occasion: Optional[str],
        include_alternative: bool,
        exclude_ids: Optional[set] = None,
    ):
        items = db.query(ClothingItem).filter(ClothingItem.user_id == user_id).all()
        target_seasons = _WEATHER_SEASONS.get(weather_tag or "", set())

        tops = cls._candidates(
            items, cls.TOP_CATEGORIES, weather_tag, occasion, exclude_ids, cls.TOP_SUBCATEGORIES
        )
        bottoms = cls._candidates(
            items, cls.BOTTOM_CATEGORIES, weather_tag, occasion, exclude_ids, cls.BOTTOM_SUBCATEGORIES
        )
        shoes = cls._candidates(items, cls.SHOE_CATEGORIES, weather_tag, occasion, exclude_ids)
        outerwear = cls._candidates(items, cls.OUTERWEAR_CATEGORIES, weather_tag, occasion, exclude_ids)

        best = cls._best_combo(tops, bottoms, shoes, target_seasons)

        chosen_top = best["top"]
        chosen_bottom = best["bottom"]
        chosen_shoes = best["shoes"]
        anchor = chosen_top or chosen_bottom or chosen_shoes

        chosen_outerwear = cls._best_outerwear(
            outerwear, anchor, target_seasons, weather_tag
        )

        alternatives: List[ClothingItem] = []
        if include_alternative and anchor is not None:
            alternatives = cls._alternatives(
                anchor,
                target_seasons,
                tops=tops,
                bottoms=bottoms,
                shoes=shoes,
                chosen={chosen_top, chosen_bottom, chosen_shoes},
            )

        rationale = cls._rationale(
            [chosen_top, chosen_bottom, chosen_shoes, chosen_outerwear],
            target_seasons,
            weather_tag,
        )

        return {
            "title": "Today's outfit suggestion",
            "weather_tag": weather_tag,
            "occasion": occasion,
            "rationale": rationale,
            "top": chosen_top,
            "bottom": chosen_bottom,
            "shoes": chosen_shoes,
            "outerwear": chosen_outerwear,
            "alternatives": alternatives,
        }

    @classmethod
    def _rationale(
        cls,
        garments: List[ClothingItem],
        target_seasons: set,
        weather_tag: Optional[str],
    ) -> Optional[str]:
        garments = [g for g in garments if g is not None]
        if not garments:
            return None
        reasons: List[str] = []

        color_pairs = [
            cls._pair_color_score(a, b)
            for a, b in combinations(garments, 2)
            if (a.color_hex or a.color) and (b.color_hex or b.color)
        ]
        if color_pairs and sum(color_pairs) / len(color_pairs) >= 0.45:
            reasons.append("the colors work together")

        formality_idxs = [
            _FORMALITY_INDEX[g.formality] for g in garments if g.formality in _FORMALITY_INDEX
        ]
        if len(formality_idxs) >= 2 and max(formality_idxs) - min(formality_idxs) <= 1:
            level = FORMALITY_LEVELS[round(sum(formality_idxs) / len(formality_idxs))]
            reasons.append(f"a consistent {level} feel")

        if target_seasons and weather_tag:
            if any(
                set(g.seasons or []) & target_seasons or "all-season" in (g.seasons or [])
                for g in garments
            ):
                reasons.append(f"pieces suited to {weather_tag} weather")

        if not reasons:
            return "Built from your freshest clean pieces."
        return "Picked because " + cls._join(reasons) + "."

    @staticmethod
    def _join(parts: List[str]) -> str:
        if len(parts) == 1:
            return parts[0]
        return ", ".join(parts[:-1]) + " and " + parts[-1]

    @classmethod
    def _best_combo(
        cls,
        tops: List[ClothingItem],
        bottoms: List[ClothingItem],
        shoes: List[ClothingItem],
        target_seasons: set,
    ) -> dict:
        top_opts = tops or [None]
        bottom_opts = bottoms or [None]
        shoe_opts = shoes or [None]

        scored = []
        for t in top_opts:
            for b in bottom_opts:
                if t is None and b is None:
                    continue
                for sh in shoe_opts:
                    score = cls._score_outfit([t, b, sh], target_seasons)
                    scored.append((score, {"top": t, "bottom": b, "shoes": sh}))

        if not scored:
            return {"top": None, "bottom": None, "shoes": None}

        best_score = max(score for score, _ in scored)
        near_best = [combo for score, combo in scored if score >= best_score - _VARIETY_MARGIN]
        return random.choice(near_best)

    @classmethod
    def _best_outerwear(
        cls,
        outerwear: List[ClothingItem],
        anchor: Optional[ClothingItem],
        target_seasons: set,
        weather_tag: Optional[str],
    ) -> Optional[ClothingItem]:
        if not outerwear:
            return None
        # Only force outerwear in cold/wet weather; otherwise include it only when
        # the weather is unknown (so a suggestion still feels complete).
        if weather_tag and weather_tag not in _COLD_WEATHER:
            return None
        if anchor is None:
            return outerwear[0]
        return max(outerwear, key=lambda ow: cls._score_outfit([anchor, ow], target_seasons))

    @classmethod
    def _alternatives(
        cls,
        anchor: ClothingItem,
        target_seasons: set,
        tops: List[ClothingItem],
        bottoms: List[ClothingItem],
        shoes: List[ClothingItem],
        chosen: set,
    ) -> List[ClothingItem]:
        def ranked(pool: List[ClothingItem], limit: int) -> List[ClothingItem]:
            remaining = [i for i in pool if i not in chosen]
            remaining.sort(
                key=lambda i: cls._score_outfit([anchor, i], target_seasons), reverse=True
            )
            return remaining[:limit]

        return ranked(tops, 2) + ranked(bottoms, 1) + ranked(shoes, 1)

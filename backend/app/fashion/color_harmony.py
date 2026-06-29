"""Color harmony for outfit matching.

Rules are loaded from `knowledge.yaml` so stylists can expand pairings without code changes.
Hex scoring uses Itten-inspired hue relationships; named colors use the YAML vocabulary.
"""

from __future__ import annotations

import colorsys
from typing import Optional

from app.fashion.knowledge import (
    classic_color_pairings,
    clashing_color_pairings,
    color_vocabulary,
)


def _vocab() -> dict[str, set[str]]:
    return color_vocabulary()


def warm_colors() -> set[str]:
    return _vocab()["warm"]


def cool_colors() -> set[str]:
    return _vocab()["cool"]


def neutral_colors() -> set[str]:
    return _vocab()["neutral"]


def normalize_color_name(color: Optional[str]) -> str:
    return (color or "").strip().lower()


def is_neutral_name(color: Optional[str]) -> bool:
    name = normalize_color_name(color)
    if not name:
        return False
    neutrals = neutral_colors()
    if name in neutrals:
        return True
    return any(token in name for token in ("gray", "grey", "beige", "cream", "nude", "off-white"))


def color_family(color: Optional[str]) -> str:
    name = normalize_color_name(color)
    if not name:
        return "unknown"
    if is_neutral_name(name):
        return "neutral"
    warm = warm_colors()
    cool = cool_colors()
    if name in warm or any(token in name for token in ("red", "orange", "yellow", "rust", "coral")):
        return "warm"
    if name in cool or any(token in name for token in ("blue", "green", "teal", "purple", "navy")):
        return "cool"
    return "unknown"


def hsv_from_hex(hex_color: Optional[str]) -> Optional[tuple[float, float, float]]:
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


def is_neutral_hsv(hsv: tuple[float, float, float]) -> bool:
    _, saturation, value = hsv
    return saturation < 0.20 or value < 0.18 or value > 0.94


def hue_distance(h1: float, h2: float) -> float:
    delta = abs(h1 - h2) % 360.0
    return min(delta, 360.0 - delta)


def pair_color_score_hex(hsv_a: tuple[float, float, float], hsv_b: tuple[float, float, float]) -> float:
    if is_neutral_hsv(hsv_a) or is_neutral_hsv(hsv_b):
        return 0.75

    h1, s1, v1 = hsv_a
    h2, s2, v2 = hsv_b
    dh = hue_distance(h1, h2)

    if dh <= 20:
        return 0.85
    if dh <= 45:
        return 0.70 if max(s1, s2) < 0.75 else 0.55
    if dh >= 150:
        muted_partner = min(s1, s2) < 0.35 or min(v1, v2) < 0.35
        if muted_partner:
            return 0.80
        if max(s1, s2) > 0.65:
            return 0.35
        return 0.65
    if 60 < dh < 120 and s1 > 0.5 and s2 > 0.5:
        return -0.55
    if 90 < dh < 150:
        return -0.25
    return 0.15


def pair_color_score_names(name_a: str, name_b: str) -> float:
    a = normalize_color_name(name_a)
    b = normalize_color_name(name_b)
    if not a or not b:
        return 0.0
    if frozenset({a, b}) in clashing_color_pairings():
        return -0.70
    if frozenset({a, b}) in classic_color_pairings():
        return 0.85
    if is_neutral_name(a) or is_neutral_name(b):
        return 0.55
    if a == b:
        return 0.65
    fam_a, fam_b = color_family(a), color_family(b)
    if fam_a == fam_b and fam_a in {"warm", "cool"}:
        return 0.45
    if {fam_a, fam_b} == {"warm", "cool"}:
        return -0.15
    return 0.10


def pair_color_score(
    hex_a: Optional[str],
    name_a: Optional[str],
    hex_b: Optional[str],
    name_b: Optional[str],
) -> float:
    hsv_a, hsv_b = hsv_from_hex(hex_a), hsv_from_hex(hex_b)
    if hsv_a and hsv_b:
        return pair_color_score_hex(hsv_a, hsv_b)
    if hsv_a and name_b and color_family(name_b) == "neutral":
        return 0.60
    if hsv_b and name_a and color_family(name_a) == "neutral":
        return 0.60
    return pair_color_score_names(name_a or "", name_b or "")


def outfit_color_score(pairs: list[tuple]) -> tuple[float, list[str]]:
    if not pairs:
        return 0.0, []
    scores = [pair_color_score(a, na, b, nb) for a, na, b, nb in pairs]
    avg = sum(scores) / len(scores)
    notes: list[str] = []
    if avg >= 0.65:
        notes.append("strong color harmony")
    elif avg >= 0.35:
        notes.append("balanced colors")
    elif avg <= -0.2:
        notes.append("color contrast needs care")
    return avg, notes

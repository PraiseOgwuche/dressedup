"""Outfit Engine v4 Phase 5 — visual coherence as a scoring signal.

Raw CLIP cosine similarity is NOT compatibility: two nearly identical tops
score ~1.0 but cannot form an outfit, and a shoe never resembles a shirt.
Measured on real FashionCLIP garment cutouts, well-matched cross-slot pairs
sit around 0.5–0.8. So the signal rewards a "sweet band" of similarity —
cohesive but distinct — and penalizes both extremes:

    cosine 0.65  -> +1.0   (visually of-a-piece, still different garments)
    cosine 0.40  ->  0.0   (drifting into different visual worlds)
    cosine 0.90  ->  0.0   (suspiciously alike)
    beyond either -> negative, clamped at -1

The outfit-level signal is the mean over pairs where both embeddings exist;
pairs without vectors are simply not counted, and an outfit with fewer than
one usable pair returns 0 (neutral — never punishes missing data).
"""

from __future__ import annotations

from itertools import combinations
from typing import TYPE_CHECKING, Sequence

from app.services.retrieval_service import item_vector

if TYPE_CHECKING:
    from app.models.clothing_item import ClothingItem

_SWEET_SPOT = 0.65
_HALF_WIDTH = 0.25  # zero-crossings at sweet spot +/- half width

# Above this cosine the pair is treated as near-duplicates and flagged.
NEAR_DUPLICATE_COSINE = 0.92


def coherence_from_cosine(cosine: float) -> float:
    """Inverted parabola over the sweet band, clamped to [-1, 1]."""
    score = 1.0 - ((cosine - _SWEET_SPOT) / _HALF_WIDTH) ** 2
    return max(-1.0, min(1.0, score))


def score_visual_coherence(
    garments: Sequence["ClothingItem"],
) -> tuple[float, list[str], list[str]]:
    """(raw score in [-1, 1], highlights, warnings) for the outfit's pairs."""
    vectors = [(g, item_vector(g)) for g in garments]
    embedded = [(g, v) for g, v in vectors if v is not None]
    if len(embedded) < 2:
        return 0.0, [], []

    scores: list[float] = []
    duplicate_pair: tuple[str, str] | None = None
    for (ga, va), (gb, vb) in combinations(embedded, 2):
        cosine = float(va @ vb)
        scores.append(coherence_from_cosine(cosine))
        if cosine >= NEAR_DUPLICATE_COSINE and duplicate_pair is None:
            duplicate_pair = (ga.name, gb.name)

    raw = sum(scores) / len(scores)

    highlights: list[str] = []
    warnings: list[str] = []
    if duplicate_pair is not None:
        warnings.append("two pieces look nearly identical")
    elif raw > 0.75:
        highlights.append("visually cohesive pieces")
    return raw, highlights, warnings

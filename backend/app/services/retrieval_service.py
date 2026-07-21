"""Outfit Engine v4 Phase 4 — hybrid candidate retrieval.

v3 fed the scorer only the ten least-worn eligible items per slot, so in a
large closet strong pieces never reached scoring at all. The hybrid pool keeps
the slot cap (combinatorial cost is unchanged) but fills it with three quotas:

  - freshness: least-worn pieces (v3's signal, keeps rotation fair)
  - visual: pieces most similar to a query vector — the locked/anchor garment
    when one exists, otherwise the closet centroid (the user's overall look)
  - exploration: a seeded random sample of the remainder, so retrieval never
    hard-locks the same shortlist

Items without a ready embedding simply compete in the other quotas; a closet
with zero embeddings degrades to exactly the freshness ordering.
"""

from __future__ import annotations

import random
from typing import List, Optional, Sequence

import numpy as np

from app.models.clothing_item import ClothingItem

FRESH_QUOTA = 4
VISUAL_QUOTA = 4
# Remaining pool slots (slot cap minus the two quotas) go to exploration.


def item_vector(item: ClothingItem) -> Optional[np.ndarray]:
    """The item's unit embedding, or None when absent/not ready."""
    if item.embedding_status != "ready" or item.embedding is None:
        return None
    vector = np.asarray(item.embedding, dtype=np.float32)
    if vector.ndim != 1 or vector.size == 0:
        return None
    return vector


def closet_centroid(items: Sequence[ClothingItem]) -> Optional[np.ndarray]:
    """Normalized mean of all ready embeddings — a proxy for the closet's look."""
    vectors = [v for v in (item_vector(i) for i in items) if v is not None]
    if not vectors:
        return None
    mean = np.mean(vectors, axis=0)
    norm = float(np.linalg.norm(mean))
    if norm < 1e-8:
        return None
    return mean / norm


def anchor_query(
    anchors: Sequence[Optional[ClothingItem]],
    fallback: Optional[np.ndarray],
) -> Optional[np.ndarray]:
    """Mean vector of the locked/anchor garments, else the fallback centroid."""
    vectors = [v for v in (item_vector(a) for a in anchors if a is not None) if v is not None]
    if not vectors:
        return fallback
    mean = np.mean(vectors, axis=0)
    norm = float(np.linalg.norm(mean))
    if norm < 1e-8:
        return fallback
    return mean / norm


def hybrid_pool(
    eligible: List[ClothingItem],
    cap: int,
    query: Optional[np.ndarray],
    rng: random.Random | None = None,
) -> List[ClothingItem]:
    """Select up to `cap` candidates from the eligible pool using the three quotas.

    `eligible` must already be hard-filtered (ownership, cleanliness, slot,
    weather/occasion). Deterministic for a fixed random state.
    """
    if len(eligible) <= cap:
        return sorted(eligible, key=lambda i: (i.times_worn or 0, i.id))

    chooser = rng or random

    picked: list[ClothingItem] = []
    picked_ids: set[int] = set()

    def take(items: Sequence[ClothingItem], count: int) -> None:
        for item in items:
            if len(picked) >= cap or count <= 0:
                return
            if item.id in picked_ids:
                continue
            picked.append(item)
            picked_ids.add(item.id)
            count -= 1

    by_freshness = sorted(eligible, key=lambda i: (i.times_worn or 0, i.id))
    take(by_freshness, FRESH_QUOTA)

    if query is not None:
        scored = []
        for item in eligible:
            vector = item_vector(item)
            if vector is None:
                continue
            scored.append((-float(vector @ query), item.id, item))
        scored.sort()
        take([item for _, _, item in scored], VISUAL_QUOTA)

    remainder = [i for i in by_freshness if i.id not in picked_ids]
    open_slots = cap - len(picked)
    if remainder and open_slots > 0:
        take(chooser.sample(remainder, min(open_slots, len(remainder))), open_slots)

    return picked

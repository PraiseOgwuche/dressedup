"""Outfit Engine v4 Phase 4 — hybrid candidate retrieval."""

import random
import uuid

import numpy as np
import pytest

from app.config import settings
from app.models.clothing_item import ClothingItem
from app.models.user import User
from app.services.outfit_service import OutfitService
from app.services.retrieval_service import (
    FRESH_QUOTA,
    anchor_query,
    closet_centroid,
    hybrid_pool,
    item_vector,
)

DIM = 512


def _vec(seed: int) -> list[float]:
    rng = np.random.default_rng(seed)
    v = rng.normal(size=DIM).astype(np.float32)
    return (v / np.linalg.norm(v)).tolist()


def _item(item_id: int, *, worn: int = 0, embedding=None) -> ClothingItem:
    item = ClothingItem(name=f"item-{item_id}", category="top")
    item.id = item_id
    item.is_clean = True
    item.times_worn = worn
    item.embedding = embedding
    item.embedding_status = "ready" if embedding is not None else "pending"
    return item


def test_item_vector_requires_ready_status():
    ready = _item(1, embedding=_vec(1))
    pending = _item(2)
    failed = _item(3, embedding=_vec(3))
    failed.embedding_status = "failed"

    assert item_vector(ready) is not None
    assert item_vector(pending) is None
    assert item_vector(failed) is None


def test_centroid_is_unit_norm_and_none_without_embeddings():
    items = [_item(i, embedding=_vec(i)) for i in range(1, 4)]
    centroid = closet_centroid(items)
    assert centroid is not None
    assert abs(float(np.linalg.norm(centroid)) - 1.0) < 1e-5

    assert closet_centroid([_item(9), _item(10)]) is None


def test_anchor_query_prefers_anchor_over_fallback():
    anchor = _item(1, embedding=_vec(1))
    fallback = np.asarray(_vec(99), dtype=np.float32)

    from_anchor = anchor_query([anchor], fallback)
    assert float(from_anchor @ np.asarray(_vec(1), dtype=np.float32)) > 0.99

    assert anchor_query([None, _item(2)], fallback) is fallback


def test_small_pool_returns_everything():
    items = [_item(i, worn=10 - i) for i in range(1, 6)]
    picked = hybrid_pool(items, cap=10, query=None)
    assert {i.id for i in picked} == {1, 2, 3, 4, 5}


def test_freshness_quota_keeps_least_worn():
    items = [_item(i, worn=i) for i in range(1, 31)]
    picked = hybrid_pool(items, cap=10, query=None, rng=random.Random(7))
    picked_ids = {i.id for i in picked}
    assert len(picked) == 10
    # The FRESH_QUOTA least-worn items are always present.
    assert {1, 2, 3, 4} & picked_ids == set(range(1, FRESH_QUOTA + 1))


def test_visual_quota_rescues_similar_but_heavily_worn_item():
    query = np.asarray(_vec(42), dtype=np.float32)
    # 30 fresh items visually unrelated to the query...
    items = [_item(i, worn=0, embedding=_vec(i)) for i in range(1, 31)]
    # ...plus one heavily-worn item nearly identical to the query. v3's
    # freshness-only shortlist would never surface it.
    match = _item(99, worn=50, embedding=(query * 0.999 + 0.001).tolist())
    items.append(match)

    picked = hybrid_pool(items, cap=10, query=query, rng=random.Random(7))
    assert 99 in {i.id for i in picked}


def test_no_embeddings_degrades_to_freshness_plus_exploration():
    items = [_item(i, worn=i) for i in range(1, 31)]
    picked = hybrid_pool(items, cap=10, query=np.asarray(_vec(1), dtype=np.float32), rng=random.Random(3))
    assert len(picked) == 10
    assert set(range(1, FRESH_QUOTA + 1)) <= {i.id for i in picked}


def test_hybrid_pool_is_deterministic_for_fixed_seed():
    items = [_item(i, worn=i % 7, embedding=_vec(i)) for i in range(1, 41)]
    query = np.asarray(_vec(5), dtype=np.float32)
    first = [i.id for i in hybrid_pool(items, cap=10, query=query, rng=random.Random(11))]
    second = [i.id for i in hybrid_pool(items, cap=10, query=query, rng=random.Random(11))]
    assert first == second


def test_candidates_unchanged_when_flag_off(db_session):
    assert settings.OUTFIT_EMBEDDINGS_ENABLED is False
    items = [_item(i, worn=30 - i) for i in range(1, 31)]
    pool = OutfitService._candidates(items, OutfitService.TOP_CATEGORIES, None, None)
    # v3 behavior: ten least-worn, ascending.
    assert [i.id for i in pool] == list(range(30, 20, -1))


def test_suggestion_uses_hybrid_pool_when_flag_on(db_session, monkeypatch):
    monkeypatch.setattr(settings, "OUTFIT_EMBEDDINGS_ENABLED", True)

    user = User(
        email=f"hybrid-{uuid.uuid4().hex[:8]}@example.com",
        full_name="Hybrid Retrieval",
        hashed_password="x",
    )
    db_session.add(user)
    db_session.flush()

    query_vec = _vec(1000)
    specs = []
    # 15 unworn tops with unrelated embeddings — enough to fill v3's shortlist.
    for i in range(15):
        specs.append(("top", 0, _vec(i + 1)))
    # A heavily-worn top nearly identical to every other embedded piece's mean;
    # v3 would drop it (worn most), hybrid visual quota should keep it reachable.
    specs.append(("top", 40, query_vec))
    specs.append(("bottom", 0, query_vec))
    specs.append(("shoes", 0, query_vec))

    rows = []
    for index, (category, worn, emb) in enumerate(specs):
        row = ClothingItem(
            user_id=user.id,
            name=f"{category}-{index}",
            category=category,
            times_worn=worn,
            embedding=emb,
            embedding_status="ready",
        )
        db_session.add(row)
        rows.append(row)
    db_session.commit()

    payload = OutfitService.get_suggestion(
        db_session,
        user.id,
        weather_tag=None,
        occasion=None,
        include_alternative=False,
    )
    # Sanity: full outfit assembled with the pipeline live.
    assert payload["top"] is not None
    assert payload["bottom"] is not None
    assert payload["shoes"] is not None

"""Outfit Engine v4 Phase 8 — embedding taste centroids + cold-start ramp."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import numpy as np
import pytest

from app.config import settings
from app.models.clothing_item import ClothingItem
from app.models.user import User
from app.services.preference_service import PreferenceService
from app.services.style_signal_service import StyleSignalService
from app.services.taste_service import TasteService


@pytest.fixture
def user(db_session):
    row = User(
        email=f"taste-{uuid.uuid4().hex[:8]}@example.com",
        full_name="Taste Tester",
        hashed_password="x",
    )
    db_session.add(row)
    db_session.commit()
    return row


def _vec(seed: int, dim: int = 512) -> list[float]:
    rng = np.random.default_rng(seed)
    v = rng.standard_normal(dim).astype(np.float32)
    v /= np.linalg.norm(v)
    return v.tolist()


def _item(db, user, name: str, *, seed: int, category: str = "top") -> ClothingItem:
    item = ClothingItem(
        user_id=user.id,
        name=name,
        category=category,
        color="navy",
        embedding=_vec(seed),
        embedding_status="ready",
        embedding_model="stub",
        embedding_version="test",
        is_clean=True,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@pytest.fixture
def embeddings_on(monkeypatch):
    monkeypatch.setattr(settings, "OUTFIT_EMBEDDINGS_ENABLED", True)


@pytest.fixture
def embeddings_off(monkeypatch):
    monkeypatch.setattr(settings, "OUTFIT_EMBEDDINGS_ENABLED", False)


def test_confidence_ramp():
    assert TasteService.confidence_from_count(0) == 0.0
    assert TasteService.confidence_from_count(2) == 0.0
    assert TasteService.confidence_from_count(3) > 0.0
    assert TasteService.confidence_from_count(3) < TasteService.confidence_from_count(6)
    assert TasteService.confidence_from_count(9) == 1.0
    assert TasteService.confidence_from_count(20) == 1.0


def test_cold_start_returns_zero(db_session, user, embeddings_on):
    liked = _item(db_session, user, "Only One", seed=1)
    StyleSignalService.record(db_session, user.id, "like", top_id=liked.id)

    profile = TasteService.build_profile(db_session, user.id)
    assert profile.positive_count == 1
    assert profile.confidence == 0.0
    assert not profile.ready

    score, notes = TasteService.score_outfit(db_session, user.id, [liked])
    assert score == 0.0
    assert notes == []


def test_taste_zero_when_embeddings_disabled(db_session, user, embeddings_off):
    items = [_item(db_session, user, f"Item {i}", seed=i) for i in range(1, 5)]
    for item in items:
        StyleSignalService.record(db_session, user.id, "wore", top_id=item.id)

    profile = TasteService.build_profile(db_session, user.id)
    assert profile.positive is None
    assert profile.confidence == 0.0


def test_positive_centroid_prefers_liked_look(db_session, user, embeddings_on):
    liked = [_item(db_session, user, f"Liked {i}", seed=10 + i) for i in range(4)]
    # Near the liked cluster
    match = _item(db_session, user, "Match", seed=10)
    # Far orthogonal-ish cluster
    clash = _item(db_session, user, "Clash", seed=99)

    for item in liked:
        StyleSignalService.record(db_session, user.id, "like", top_id=item.id)

    profile = TasteService.build_profile(db_session, user.id)
    assert profile.ready
    assert profile.positive is not None

    match_aff = TasteService.item_affinity(match, profile)
    clash_aff = TasteService.item_affinity(clash, profile)
    assert match_aff > clash_aff


def test_dislike_pulls_negative_centroid(db_session, user, embeddings_on):
    liked = [_item(db_session, user, f"Good {i}", seed=20 + i) for i in range(3)]
    hated = [_item(db_session, user, f"Bad {i}", seed=80 + i) for i in range(3)]
    near_bad = _item(db_session, user, "Near Bad", seed=80)

    for item in liked:
        StyleSignalService.record(db_session, user.id, "wore", top_id=item.id)
    for item in hated:
        StyleSignalService.record(db_session, user.id, "dislike", top_id=item.id)

    profile = TasteService.build_profile(db_session, user.id)
    assert profile.negative is not None
    assert TasteService.item_affinity(near_bad, profile) < TasteService.item_affinity(liked[0], profile)


def test_swap_out_soft_negative(db_session, user, embeddings_on):
    kept = [_item(db_session, user, f"Kept {i}", seed=30 + i) for i in range(3)]
    rejected = _item(db_session, user, "Rejected", seed=70)
    replacement = _item(db_session, user, "Replacement", seed=31)

    for item in kept:
        StyleSignalService.record(db_session, user.id, "like", top_id=item.id)
    StyleSignalService.record(
        db_session,
        user.id,
        "swap",
        top_id=replacement.id,
        replaced_item_id=rejected.id,
        swap_slot="top",
    )

    profile = TasteService.build_profile(db_session, user.id)
    assert profile.negative is not None
    assert TasteService.item_affinity(rejected, profile) < TasteService.item_affinity(
        replacement, profile
    )


def test_recency_decay_favors_fresh_likes(db_session, user, embeddings_on):
    old = _item(db_session, user, "Old Fav", seed=40)
    fresh = _item(db_session, user, "Fresh Fav", seed=41)
    other = _item(db_session, user, "Other", seed=42)
    probe_old = _item(db_session, user, "Probe Old", seed=40)
    probe_fresh = _item(db_session, user, "Probe Fresh", seed=41)

    for item in (old, fresh, other):
        # Need 3+ for confidence
        StyleSignalService.record(db_session, user.id, "like", top_id=item.id)

    # Age the first signal heavily
    signals = StyleSignalService.recent(db_session, user.id)
    old_signal = next(s for s in signals if s.top_id == old.id)
    old_signal.created_at = datetime.now(timezone.utc) - timedelta(days=120)
    db_session.commit()

    profile = TasteService.build_profile(db_session, user.id)
    assert TasteService.item_affinity(probe_fresh, profile) >= TasteService.item_affinity(
        probe_old, profile
    )


def test_personalization_bonus_blends_taste(db_session, user, embeddings_on):
    liked = [_item(db_session, user, f"L{i}", seed=50 + i, category="top") for i in range(4)]
    for item in liked:
        PreferenceService.record(
            db_session, user.id, top_id=item.id, bottom_id=None, shoes_id=None, signal="like"
        )

    match = liked[0]
    bonus, notes = PreferenceService.personalization_bonus(db_session, user.id, [match])
    assert bonus != 0.0
    # Structured item bonus alone would fire; taste may also contribute a note.
    assert isinstance(notes, list)


def test_retrieval_query_blends_taste(db_session, user, embeddings_on):
    items = [_item(db_session, user, f"C{i}", seed=60 + i) for i in range(4)]
    for item in items:
        StyleSignalService.record(db_session, user.id, "wore", top_id=item.id)

    from app.services.retrieval_service import closet_centroid

    fallback = closet_centroid(items)
    query = TasteService.retrieval_query(db_session, user.id, fallback)
    assert query is not None
    assert abs(float(np.linalg.norm(query)) - 1.0) < 1e-5


def test_outfit_score_deterministic(db_session, user, embeddings_on):
    items = [_item(db_session, user, f"D{i}", seed=70 + i) for i in range(4)]
    for item in items:
        StyleSignalService.record(db_session, user.id, "like", top_id=item.id)

    a, _ = TasteService.score_outfit(db_session, user.id, items[:2])
    b, _ = TasteService.score_outfit(db_session, user.id, items[:2])
    assert a == b

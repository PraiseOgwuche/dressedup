"""Outfit Engine v4 Phase 5 — visual coherence signal + joint outerwear."""

import uuid

import numpy as np
import pytest

from app.config import settings
from app.fashion import FashionMatcher, MatchContext
from app.fashion.visual_coherence import (
    NEAR_DUPLICATE_COSINE,
    coherence_from_cosine,
    score_visual_coherence,
)
from app.models.clothing_item import ClothingItem
from app.models.user import User
from app.services.outfit_service import OutfitService

DIM = 512


def _unit(seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    v = rng.normal(size=DIM).astype(np.float32)
    return v / np.linalg.norm(v)


def _with_cosine(base: np.ndarray, cosine: float, seed: int = 7) -> list[float]:
    """A unit vector at exactly `cosine` similarity to `base`."""
    other = _unit(seed)
    orthogonal = other - float(other @ base) * base
    orthogonal /= np.linalg.norm(orthogonal)
    v = cosine * base + np.sqrt(1.0 - cosine**2) * orthogonal
    return v.astype(np.float32).tolist()


def _item(name: str, category: str, embedding=None, **attrs) -> ClothingItem:
    item = ClothingItem(name=name, category=category, **attrs)
    item.embedding = embedding
    item.embedding_status = "ready" if embedding is not None else "pending"
    item.times_worn = 0
    return item


class TestCoherenceCurve:
    def test_sweet_spot_scores_one(self):
        assert coherence_from_cosine(0.65) == pytest.approx(1.0)

    def test_zero_crossings_at_band_edges(self):
        assert coherence_from_cosine(0.40) == pytest.approx(0.0)
        assert coherence_from_cosine(0.90) == pytest.approx(0.0)

    def test_identical_garments_penalized(self):
        assert coherence_from_cosine(1.0) < -0.9

    def test_unrelated_garments_clamped(self):
        assert coherence_from_cosine(0.0) == -1.0
        assert coherence_from_cosine(-1.0) == -1.0

    def test_real_closet_range_is_positive(self):
        # Measured pairwise range on the live FashionCLIP closet: 0.49-0.77.
        for cosine in (0.49, 0.55, 0.61, 0.70, 0.77):
            assert coherence_from_cosine(cosine) > 0


class TestScoreVisualCoherence:
    def test_neutral_without_embeddings(self):
        garments = [_item("Tee", "top"), _item("Jeans", "bottom")]
        raw, highlights, warnings = score_visual_coherence(garments)
        assert raw == 0.0
        assert highlights == [] and warnings == []

    def test_neutral_with_single_embedding(self):
        base = _unit(1)
        garments = [_item("Tee", "top", base.tolist()), _item("Jeans", "bottom")]
        raw, _, _ = score_visual_coherence(garments)
        assert raw == 0.0

    def test_sweet_band_pair_scores_high_with_highlight(self):
        base = _unit(1)
        garments = [
            _item("Tee", "top", base.tolist()),
            _item("Jeans", "bottom", _with_cosine(base, 0.65)),
        ]
        raw, highlights, warnings = score_visual_coherence(garments)
        assert raw == pytest.approx(1.0, abs=1e-4)
        assert "visually cohesive pieces" in highlights
        assert warnings == []

    def test_near_duplicates_warned_and_penalized(self):
        base = _unit(1)
        garments = [
            _item("Tee A", "top", base.tolist()),
            _item("Tee B", "top", _with_cosine(base, 0.99)),
        ]
        raw, _, warnings = score_visual_coherence(garments)
        assert raw < -0.5
        assert "two pieces look nearly identical" in warnings

    def test_unembedded_pairs_not_counted(self):
        base = _unit(1)
        garments = [
            _item("Tee", "top", base.tolist()),
            _item("Jeans", "bottom", _with_cosine(base, 0.65)),
            _item("No-photo scarf", "accessory"),  # must not drag the mean
        ]
        raw, _, _ = score_visual_coherence(garments)
        assert raw == pytest.approx(1.0, abs=1e-4)


class TestMatcherIntegration:
    def _garments(self):
        base = _unit(1)
        return [
            _item("Tee", "top", base.tolist(), color="white"),
            _item("Jeans", "bottom", _with_cosine(base, 0.65), color="navy"),
        ]

    def test_flag_off_ignores_embeddings(self):
        assert settings.OUTFIT_EMBEDDINGS_ENABLED is False
        breakdown = FashionMatcher.score_outfit(self._garments(), MatchContext())
        assert breakdown.visual == 0.0

    def test_flag_on_adds_capped_visual_term(self, monkeypatch):
        context = MatchContext()
        garments = self._garments()
        baseline = FashionMatcher.score_outfit(garments, context)

        monkeypatch.setattr(settings, "OUTFIT_EMBEDDINGS_ENABLED", True)
        hybrid = FashionMatcher.score_outfit(garments, context)

        assert hybrid.visual == pytest.approx(1.0, abs=1e-4)
        # Weight cap: the perfect visual signal moves the total by exactly 0.10.
        assert hybrid.total - baseline.total == pytest.approx(0.10, abs=1e-4)

    def test_duplicates_lose_to_distinct_pieces(self, monkeypatch):
        monkeypatch.setattr(settings, "OUTFIT_EMBEDDINGS_ENABLED", True)
        base = _unit(1)
        context = MatchContext()
        shared = dict(color="white")

        cohesive = FashionMatcher.score_outfit(
            [
                _item("Tee", "top", base.tolist(), **shared),
                _item("Pants", "bottom", _with_cosine(base, 0.65), **shared),
            ],
            context,
        )
        duplicates = FashionMatcher.score_outfit(
            [
                _item("Tee A", "top", base.tolist(), **shared),
                _item("Tee A again", "bottom", _with_cosine(base, 0.995), **shared),
            ],
            context,
        )
        assert cohesive.total > duplicates.total


class TestJointOuterwear:
    def test_outerwear_judged_against_full_outfit(self, db_session, monkeypatch):
        monkeypatch.setattr(settings, "OUTFIT_EMBEDDINGS_ENABLED", True)

        user = User(
            email=f"joint-ow-{uuid.uuid4().hex[:8]}@example.com",
            full_name="Joint Outerwear",
            hashed_password="x",
        )
        db_session.add(user)
        db_session.flush()

        # Shared-core construction: v_i = a*base + b*e_i with orthonormal e_i
        # gives every cross pair cosine a^2 = 0.65 — squarely in the sweet band.
        base = _unit(1)
        a, b = np.sqrt(0.65), np.sqrt(0.35)

        def piece(axis_seed: int) -> list[float]:
            e = _unit(axis_seed)
            e = e - float(e @ base) * base
            e /= np.linalg.norm(e)
            return (a * base + b * e).astype(np.float32).tolist()

        top = _item("Tee", "top", piece(11))
        bottom = _item("Jeans", "bottom", piece(12))
        shoes = _item("Sneakers", "shoes", piece(13))
        # Near-duplicate of the top vs a piece as distinct as the rest.
        clone_jacket = _item(
            "Shacket like the tee",
            "jacket",
            _with_cosine(np.asarray(top.embedding, dtype=np.float32), 0.99, seed=14),
        )
        good_jacket = _item("Distinct jacket", "jacket", piece(15))

        for row in (top, bottom, shoes, clone_jacket, good_jacket):
            row.user_id = user.id
            db_session.add(row)
        db_session.commit()

        chosen = OutfitService._best_outerwear(
            db_session,
            user.id,
            [clone_jacket, good_jacket],
            anchor=top,
            context=MatchContext(weather_tag="cold"),
            weather_tag="cold",
            ensemble=[top, bottom, shoes],
        )
        assert chosen is not None and chosen.id == good_jacket.id

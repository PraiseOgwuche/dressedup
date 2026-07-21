"""Outfit Engine v4 Phase 7 — three distinct styling directions.

Completion bar: the three results are valid, visually distinct, and not
simple one-item substitutions of each other.
"""

import uuid

import pytest

from app.fashion.context import MatchContext
from app.fashion.direction_profiles import (
    DIRECTIONS,
    garment_direction_affinity,
    score_direction,
)
from app.fashion.matcher import FashionMatcher
from app.models.clothing_item import ClothingItem
from app.models.user import User
from app.services.outfit_service import OutfitService


@pytest.fixture
def user(db_session):
    row = User(
        email=f"directions-{uuid.uuid4().hex[:8]}@example.com",
        full_name="Directions Tester",
        hashed_password="x",
    )
    db_session.add(row)
    db_session.commit()
    return row


def _add(db, user, name, category, subcategory=None, **attrs):
    item = ClothingItem(
        user_id=user.id, name=name, category=category, subcategory=subcategory, **attrs
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def _closet(db, user):
    """A wardrobe wide enough that each direction has a natural home."""
    # Classic candidates: neutral, solid, smart.
    _add(db, user, "White Oxford Shirt", "top", "shirt", color="white",
         pattern="solid", formality="smart-casual", material="cotton poplin")
    _add(db, user, "Charcoal Trousers", "bottom", "trousers", color="charcoal",
         pattern="solid", formality="smart-casual", material="wool blend")
    _add(db, user, "Black Loafers", "shoes", "loafers", color="black",
         pattern="solid", formality="smart-casual", material="leather")
    # Expressive candidates: color + statement pattern.
    _add(db, user, "Red Graphic Tee", "top", "t-shirt", color="red",
         pattern="graphic", formality="casual", material="cotton")
    _add(db, user, "Plaid Statement Trousers", "bottom", "trousers", color="green",
         pattern="plaid", formality="casual", material="cotton twill")
    _add(db, user, "Orange High-Tops", "sneakers", "high-top", color="orange",
         pattern="solid", formality="casual", material="canvas")
    # Relaxed candidates: soft, casual, comfortable.
    _add(db, user, "Grey Oversized Hoodie", "top", "hoodie", color="grey",
         pattern="solid", formality="loungewear", material="fleece")
    _add(db, user, "Beige Jogger Sweatpants", "bottom", "joggers", color="beige",
         pattern="solid", formality="loungewear", material="cotton jersey")
    _add(db, user, "White Slip-On Sneakers", "sneakers", "slip-on", color="white",
         pattern="solid", formality="casual", material="canvas")


# ---------------------------------------------------------------------------
# Direction profiles (garment affinity)
# ---------------------------------------------------------------------------

def _garment(**attrs) -> ClothingItem:
    item = ClothingItem(name=attrs.pop("name", "x"), category=attrs.pop("category", "top"))
    for key, value in attrs.items():
        setattr(item, key, value)
    return item


def test_classic_rewards_neutral_solids_over_statement_pieces():
    quiet = _garment(color="navy", pattern="solid", formality="smart-casual")
    loud = _garment(color="orange", pattern="graphic", formality="casual")
    assert garment_direction_affinity(quiet, "classic") > garment_direction_affinity(loud, "classic")


def test_expressive_rewards_statement_pieces_over_neutral_solids():
    quiet = _garment(color="navy", pattern="solid", formality="smart-casual")
    loud = _garment(color="orange", pattern="graphic", formality="casual")
    assert garment_direction_affinity(loud, "expressive") > garment_direction_affinity(quiet, "expressive")


def test_relaxed_rewards_soft_casual_over_structured_formal():
    comfy = _garment(
        name="Oversized Hoodie", subcategory="hoodie",
        formality="loungewear", material="fleece",
    )
    stiff = _garment(
        name="Tweed Blazer", subcategory="blazer",
        formality="business-casual", material="wool tweed",
    )
    assert garment_direction_affinity(comfy, "relaxed") > garment_direction_affinity(stiff, "relaxed")


def test_relaxed_prefers_casual_footwear():
    sneakers = _garment(name="Slip-On Sneakers", category="sneakers",
                        subcategory="slip-on", formality="casual")
    heels = _garment(name="Stiletto Heels", category="heels",
                     subcategory="heels", formality="formal")
    assert garment_direction_affinity(sneakers, "relaxed") > garment_direction_affinity(heels, "relaxed")


def test_score_direction_neutral_without_direction():
    garments = [_garment(color="red", pattern="graphic")]
    assert score_direction(garments, None) == (0.0, [])
    assert score_direction(garments, "not-a-direction") == (0.0, [])


def test_matcher_unchanged_when_no_direction_requested():
    """Default path (direction=None) must not shift a single score."""
    garments = [
        _garment(name="Tee", category="top", color="white", pattern="solid", formality="casual"),
        _garment(name="Jeans", category="bottom", color="navy", pattern="solid", formality="casual"),
    ]
    plain = FashionMatcher.score_outfit(garments, MatchContext())
    assert plain.direction == 0.0

    directed = FashionMatcher.score_outfit(garments, MatchContext(direction="expressive"))
    assert directed.direction != 0.0 or directed.total == plain.total


def test_matcher_direction_reorders_totals():
    quiet = [
        _garment(name="Oxford", category="top", color="white", pattern="solid", formality="smart-casual"),
        _garment(name="Trousers", category="bottom", color="charcoal", pattern="solid", formality="smart-casual"),
    ]
    loud = [
        _garment(name="Graphic Tee", category="top", color="red", pattern="graphic", formality="casual"),
        _garment(name="Plaid Pants", category="bottom", color="green", pattern="plaid", formality="casual"),
    ]
    classic_ctx = MatchContext(direction="classic")
    expressive_ctx = MatchContext(direction="expressive")

    quiet_gap = (
        FashionMatcher.score_outfit(quiet, classic_ctx).total
        - FashionMatcher.score_outfit(quiet, expressive_ctx).total
    )
    loud_gap = (
        FashionMatcher.score_outfit(loud, classic_ctx).total
        - FashionMatcher.score_outfit(loud, expressive_ctx).total
    )
    # The quiet outfit should benefit from classic scoring relative to
    # expressive scoring, and vice versa for the loud outfit.
    assert quiet_gap > 0
    assert loud_gap < 0


# ---------------------------------------------------------------------------
# Engine: get_directions
# ---------------------------------------------------------------------------

def test_directions_returns_three_valid_outfits(db_session, user):
    _closet(db_session, user)
    payload = OutfitService.get_directions(db_session, user.id, weather_tag=None, occasion=None)

    assert [d["direction"] for d in payload["directions"]] == list(DIRECTIONS)
    for look in payload["directions"]:
        assert look["label"] and look["tagline"]
        # Valid structure: shoes plus either a dress or at least one separate.
        assert look["shoes"] is not None
        assert look["dress"] is not None or look["top"] is not None or look["bottom"] is not None
        if look["dress"] is not None:
            assert look["top"] is None and look["bottom"] is None


def test_directions_are_not_one_item_substitutions(db_session, user):
    _closet(db_session, user)
    payload = OutfitService.get_directions(db_session, user.id, weather_tag=None, occasion=None)

    looks = payload["directions"]
    assert len(looks) == 3

    def ids(look):
        return {
            look[slot].id
            for slot in ("dress", "top", "bottom", "shoes")
            if look[slot] is not None
        }

    for i in range(len(looks)):
        for j in range(i + 1, len(looks)):
            shared = ids(looks[i]) & ids(looks[j])
            assert len(shared) <= 1, (
                f"{looks[i]['direction']} and {looks[j]['direction']} share {shared}"
            )


def test_directions_pick_on_profile(db_session, user):
    """Each direction should land on the pieces built for it."""
    _closet(db_session, user)
    payload = OutfitService.get_directions(db_session, user.id, weather_tag=None, occasion=None)
    by_direction = {d["direction"]: d for d in payload["directions"]}

    assert by_direction["classic"]["top"].name == "White Oxford Shirt"
    assert by_direction["expressive"]["top"].name == "Red Graphic Tee"
    assert by_direction["relaxed"]["top"].name == "Grey Oversized Hoodie"


def test_directions_deterministic(db_session, user):
    _closet(db_session, user)

    def snapshot():
        payload = OutfitService.get_directions(db_session, user.id, weather_tag=None, occasion=None)
        return [
            (
                look["direction"],
                *(look[slot].id if look[slot] else None for slot in ("dress", "top", "bottom", "shoes")),
            )
            for look in payload["directions"]
        ]

    assert snapshot() == snapshot() == snapshot()


def test_directions_small_closet_still_returns_three(db_session, user):
    """With one item per slot, overlap is unavoidable — never crash, still 3 looks."""
    _add(db_session, user, "Tee", "top", color="white", pattern="solid", formality="casual")
    _add(db_session, user, "Jeans", "bottom", color="navy", pattern="solid", formality="casual")
    _add(db_session, user, "Sneakers", "sneakers", color="white", pattern="solid", formality="casual")

    payload = OutfitService.get_directions(db_session, user.id, weather_tag=None, occasion=None)
    assert len(payload["directions"]) == 3
    for look in payload["directions"]:
        assert look["top"] is not None and look["bottom"] is not None


def test_directions_empty_closet(db_session, user):
    payload = OutfitService.get_directions(db_session, user.id, weather_tag=None, occasion=None)
    assert payload["directions"] == []

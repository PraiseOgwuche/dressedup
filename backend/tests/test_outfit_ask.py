"""Outfit Engine v4 Phase 9 — grounded natural-language styling."""

from __future__ import annotations

import uuid

import pytest

from app.models.clothing_item import ClothingItem
from app.models.user import User
from app.services.outfit_ask_service import fulfill_outfit_ask, parse_outfit_query
from app.services.outfit_service import OutfitService


@pytest.fixture
def user(db_session):
    row = User(
        email=f"ask-{uuid.uuid4().hex[:8]}@example.com",
        full_name="Ask Tester",
        hashed_password="x",
    )
    db_session.add(row)
    db_session.commit()
    return row


def _add(db, user, name, category, subcategory=None, **attrs):
    item = ClothingItem(
        user_id=user.id,
        name=name,
        category=category,
        subcategory=subcategory,
        is_clean=True,
        **attrs,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def _closet(db, user):
    return {
        "trousers": _add(
            db, user, "Navy Wool Trousers", "bottom", "trousers", color="navy", times_worn=2
        ),
        "jeans": _add(db, user, "Blue Jeans", "bottom", "jeans", color="blue", times_worn=5),
        "tee": _add(db, user, "White Tee", "top", "t-shirt", color="white", times_worn=1),
        "shirt": _add(
            db, user, "Oxford Shirt", "top", "shirt", color="white", formality="smart-casual", times_worn=3
        ),
        "sneakers": _add(
            db, user, "White Sneakers", "sneakers", "sneakers", color="white", times_worn=8
        ),
        "loafers": _add(
            db, user, "Black Loafers", "shoes", "loafers", color="black", times_worn=1
        ),
        "fresh_jacket": _add(
            db, user, "Fresh Bomber", "jacket", "jacket", color="black", times_worn=0
        ),
        "worn_jacket": _add(
            db, user, "Worn Blazer", "jacket", "blazer", color="navy", times_worn=12
        ),
    }


# --- Parser (backward compatible) ---

def test_parse_work_cold_quiet_luxury():
    parsed = parse_outfit_query("Dress me for a cold work day with quiet luxury vibes")
    assert parsed.occasion == "work"
    assert parsed.weather_tag == "cold"
    assert parsed.trend == "quiet-luxury"
    assert "work" in parsed.interpretation.lower()


def test_parse_date_night_streetwear():
    parsed = parse_outfit_query("Outfit for date night, streetwear")
    assert parsed.occasion == "date"
    assert parsed.trend == "streetwear"


def test_parse_rainy_party():
    parsed = parse_outfit_query("Going to a party and it might rain")
    assert parsed.occasion == "party"
    assert parsed.weather_tag == "rainy"


def test_parse_empty_defaults():
    parsed = parse_outfit_query("   ")
    assert parsed.occasion is None
    assert "tell me" in parsed.interpretation.lower()


def test_parse_gym_hot():
    parsed = parse_outfit_query("Gym session, hot weather")
    assert parsed.occasion == "workout"
    assert parsed.weather_tag == "hot"


def test_parse_exclusions_and_direction():
    parsed = parse_outfit_query("Something relaxed, but not sneakers")
    assert parsed.direction == "relaxed"
    assert "sneakers" in parsed.excluded_tokens


def test_parse_business_casual_formality():
    parsed = parse_outfit_query("Business-casual dinner")
    assert parsed.formality in {"smart-casual", "business"}
    assert parsed.occasion in {"work", "date"}


# --- Closet-grounded resolution ---

def test_resolve_anchor_navy_trousers(db_session, user):
    pieces = _closet(db_session, user)
    parsed = parse_outfit_query(
        "Business-casual dinner centered on my navy trousers",
        closet=list(pieces.values()),
    )
    assert parsed.anchor_item_id == pieces["trousers"].id
    assert parsed.anchor_label
    assert "trousers" in parsed.interpretation.lower() or "navy" in parsed.interpretation.lower()


def test_resolve_exclude_sneakers(db_session, user):
    pieces = _closet(db_session, user)
    parsed = parse_outfit_query(
        "Something relaxed, but not sneakers",
        closet=list(pieces.values()),
    )
    assert pieces["sneakers"].id in parsed.exclude_item_ids
    assert pieces["loafers"].id not in parsed.exclude_item_ids


def test_resolve_freshness_jacket(db_session, user):
    pieces = _closet(db_session, user)
    parsed = parse_outfit_query(
        "Use the jacket I haven't worn recently",
        closet=list(pieces.values()),
    )
    assert parsed.anchor_item_id == pieces["fresh_jacket"].id
    assert parsed.freshness_slot == "outerwear"


# --- Fulfillment: real IDs only, engine-validated ---

def test_ask_anchors_real_closet_item(db_session, user):
    pieces = _closet(db_session, user)
    result = fulfill_outfit_ask(
        db_session, user.id, "Dinner centered on my navy trousers"
    )
    suggestion = result["suggestion"]
    assert suggestion["bottom"].id == pieces["trousers"].id
    # Every piece is owned.
    owned = {p.id for p in pieces.values()}
    for slot in ("top", "bottom", "shoes", "outerwear", "dress"):
        piece = suggestion.get(slot)
        if piece is not None:
            assert piece.id in owned


def test_ask_never_returns_excluded_sneakers(db_session, user):
    pieces = _closet(db_session, user)
    # Run a few times — exclusions must always hold.
    for _ in range(8):
        result = fulfill_outfit_ask(
            db_session, user.id, "Everyday look, but not sneakers"
        )
        shoes = result["suggestion"].get("shoes")
        if shoes is not None:
            assert shoes.id != pieces["sneakers"].id


def test_ask_does_not_invent_items(db_session, user):
    pieces = _closet(db_session, user)
    result = fulfill_outfit_ask(db_session, user.id, "Dress me for a cold work day")
    owned = {p.id for p in pieces.values()}
    suggestion = result["suggestion"]
    for slot in ("dress", "top", "bottom", "shoes", "outerwear", "bag", "accessory", "headwear"):
        piece = suggestion.get(slot)
        if piece is not None:
            assert piece.id in owned


def test_ask_without_closet_still_parses(db_session, user):
    result = fulfill_outfit_ask(db_session, user.id, "Cold work day, quiet luxury")
    assert result["parsed"].occasion == "work"
    assert result["parsed"].weather_tag == "cold"
    # Empty closet → suggestion with empty slots is fine.
    assert result["suggestion"] is not None


def test_outfit_ask_endpoint(client, auth_header, db_session):
    # Seed a minimal closet for the authenticated test user.
    from app.models.user import User as UserModel

    me = db_session.query(UserModel).filter(UserModel.email.contains("@")).first()
    assert me is not None
    _add(db_session, me, "Tee", "top", color="white")
    _add(db_session, me, "Jeans", "bottom", "jeans", color="blue")
    _add(db_session, me, "Sneakers", "sneakers", color="white")

    response = client.post(
        "/api/v1/outfits/ask",
        headers=auth_header,
        json={"query": "Dress me for work on a cold day, quiet luxury"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["parsed"]["occasion"] == "work"
    assert body["parsed"]["weather_tag"] == "cold"
    assert body["parsed"]["trend"] == "quiet-luxury"
    assert "suggestion" in body
    assert body["suggestion"]["title"]
    # New Phase 9 fields present.
    assert "anchor_item_id" in body["parsed"]
    assert "excluded_tokens" in body["parsed"]


def test_get_suggestion_accepts_direction(db_session, user):
    _closet(db_session, user)
    payload = OutfitService.get_suggestion(
        db_session,
        user.id,
        weather_tag=None,
        occasion=None,
        include_alternative=False,
        direction="relaxed",
    )
    assert payload["top"] is not None or payload["dress"] is not None

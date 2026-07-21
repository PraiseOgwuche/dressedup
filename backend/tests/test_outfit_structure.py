"""Outfit Engine v4 Phase 6 — full-body garments + optional accessory slots."""

import uuid

import pytest

from app.models.clothing_item import ClothingItem
from app.models.user import User
from app.services.outfit_service import OutfitService


@pytest.fixture
def user(db_session):
    row = User(
        email=f"structure-{uuid.uuid4().hex[:8]}@example.com",
        full_name="Structure Tester",
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


def test_slot_for_item_maps_new_categories(db_session, user):
    cases = {
        ("dress", "midi"): "dress",
        ("dress", "jumpsuit"): "dress",
        ("bag", "tote"): "bag",
        ("jewelry", "necklace"): "accessory",
        ("accessory", "belt"): "accessory",
        ("headwear", "hat"): "headwear",
    }
    for (category, subcategory), expected in cases.items():
        item = ClothingItem(name="x", category=category, subcategory=subcategory)
        assert OutfitService.slot_for_item(item) == expected, (category, subcategory)


def test_dress_only_closet_generates_dress_outfit(db_session, user):
    _add(db_session, user, "Black Midi Dress", "dress", "midi", color="black")
    _add(db_session, user, "Black Heels", "heels", color="black")

    payload = OutfitService.get_suggestion(
        db_session, user.id, weather_tag=None, occasion=None, include_alternative=False
    )
    assert payload["dress"] is not None and payload["dress"].name == "Black Midi Dress"
    assert payload["top"] is None
    assert payload["bottom"] is None
    assert payload["shoes"] is not None


def test_dress_never_combined_with_separates(db_session, user):
    _add(db_session, user, "Sundress", "dress", "midi", color="yellow")
    _add(db_session, user, "Linen Shirt", "top", color="white")
    _add(db_session, user, "Chino Shorts", "bottom", "shorts", color="tan")
    _add(db_session, user, "Sneakers", "sneakers", color="white")

    for _ in range(15):
        payload = OutfitService.get_suggestion(
            db_session, user.id, weather_tag=None, occasion=None, include_alternative=False
        )
        if payload["dress"] is not None:
            assert payload["top"] is None and payload["bottom"] is None
        else:
            assert payload["top"] is not None or payload["bottom"] is not None


def test_accessory_slots_default_to_none(db_session, user):
    _add(db_session, user, "Tee", "top", color="white")
    _add(db_session, user, "Jeans", "bottom", color="navy")

    payload = OutfitService.get_suggestion(
        db_session, user.id, weather_tag=None, occasion=None, include_alternative=False
    )
    for slot in ("bag", "accessory", "headwear"):
        assert slot in payload
        assert payload[slot] is None or payload[slot].id is not None


def test_accessories_attach_without_being_forced(db_session, user):
    _add(db_session, user, "Tee", "top", color="white")
    _add(db_session, user, "Jeans", "bottom", color="navy")
    _add(db_session, user, "Sneakers", "sneakers", color="white")
    bag = _add(db_session, user, "Leather Tote", "bag", "tote", color="tan")

    payload = OutfitService.get_suggestion(
        db_session, user.id, weather_tag=None, occasion=None, include_alternative=False
    )
    # The bag may or may not improve the score, but it must never displace a
    # core slot and never be some other garment.
    assert payload["top"] is not None
    assert payload["bottom"] is not None
    if payload["bag"] is not None:
        assert payload["bag"].id == bag.id


def test_suggest_around_dress_locks_it(db_session, user):
    dress = _add(db_session, user, "Slip Dress", "dress", "midi", color="black")
    _add(db_session, user, "Heels", "heels", color="black")
    _add(db_session, user, "Tee", "top", color="white")

    payload = OutfitService.suggest_around_item(db_session, user.id, dress.id)
    assert payload is not None
    assert payload["dress"].id == dress.id
    assert payload["top"] is None and payload["bottom"] is None


def test_suggest_around_accessory_builds_full_look(db_session, user):
    _add(db_session, user, "Tee", "top", color="white")
    _add(db_session, user, "Jeans", "bottom", color="navy")
    _add(db_session, user, "Sneakers", "sneakers", color="white")
    hat = _add(db_session, user, "Wool Beanie", "headwear", "hat", color="gray")

    payload = OutfitService.suggest_around_item(db_session, user.id, hat.id)
    assert payload is not None
    assert payload["headwear"].id == hat.id
    assert payload["top"] is not None and payload["bottom"] is not None


def test_dress_swap_excludes_current_dress(db_session, user):
    slip = _add(db_session, user, "Slip Dress", "dress", "midi", color="black")
    _add(db_session, user, "Wrap Dress", "dress", "midi", color="red")
    _add(db_session, user, "Heels", "heels", color="black")

    payload = OutfitService.get_suggestion(
        db_session,
        user.id,
        weather_tag=None,
        occasion=None,
        include_alternative=False,
        swap_slot="dress",
        dress_id=slip.id,
    )
    assert payload["dress"] is not None
    assert payload["dress"].id != slip.id


def test_feedback_accepts_dress_id(client, auth_header):
    item = client.post(
        "/api/v1/closet/items",
        json={"name": "Midi Dress", "category": "dress", "subcategory": "midi"},
        headers=auth_header,
    ).json()
    response = client.post(
        "/api/v1/outfits/feedback",
        json={"dress_id": item["id"], "signal": "like"},
        headers=auth_header,
    )
    assert response.status_code == 201

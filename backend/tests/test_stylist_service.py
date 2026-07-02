import uuid

from app.models.clothing_item import ClothingItem
from app.models.user import User
from app.services.stylist_service import StylistService


def test_rule_based_gap_insight_prefers_missing_bottoms(db_session):
    user = User(
        email=f"stylist-{uuid.uuid4().hex[:6]}@example.com",
        full_name="Stylist Test",
        hashed_password="x",
    )
    db_session.add(user)
    db_session.flush()
    db_session.add(
        ClothingItem(
            user_id=user.id,
            name="Only top",
            category="top",
            is_clean=True,
            source="manual",
        )
    )
    db_session.commit()

    closet = StylistService.closet_snapshot(db_session, user.id)
    insight = StylistService.rule_based_gap_insight(closet)
    assert "bottom" in insight.lower() or "anchor" in insight.lower()


def test_stylist_stub_returns_none_for_outfit(db_session):
    user = User(
        email=f"stylist-{uuid.uuid4().hex[:7]}@example.com",
        full_name="Stylist Test",
        hashed_password="x",
    )
    db_session.add(user)
    db_session.commit()

    note = StylistService.enhance_outfit(
        db_session,
        user.id,
        top=None,
        bottom=None,
        shoes=None,
        outerwear=None,
        occasion="everyday",
        weather_tag="mild",
        trend=None,
        rule_rationale="Neutral combo.",
    )
    assert note is None

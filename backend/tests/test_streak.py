from datetime import UTC, date, datetime, timedelta

from app.models.outfit_feedback import SIGNAL_WORE
from app.services.streak_service import (
    _collect_active_dates,
    _current_streak,
    _longest_streak,
    _to_local_date,
)


def test_streak_helpers():
    dates = [date(2026, 6, 27), date(2026, 6, 28), date(2026, 6, 29)]
    assert _current_streak(dates, date(2026, 6, 29)) == 3
    assert _current_streak(dates, date(2026, 6, 30)) == 3
    assert _current_streak(dates, date(2026, 7, 1)) == 0
    assert _longest_streak(dates) == 3
    assert _longest_streak([date(2026, 1, 1), date(2026, 1, 3), date(2026, 1, 4)]) == 2


def test_streak_endpoint(client, auth_header):
    top = client.post(
        "/api/v1/closet/items",
        json={"name": "Streak tee", "category": "Top"},
        headers=auth_header,
    ).json()
    client.post(
        "/api/v1/outfits/feedback",
        json={"top_id": top["id"], "signal": "wore"},
        headers=auth_header,
    )

    streak = client.get("/api/v1/social/streak", headers=auth_header)
    assert streak.status_code == 200
    payload = streak.json()
    assert payload["current_streak"] >= 1
    assert payload["total_fit_days"] >= 1
    assert payload["longest_streak"] >= 1
    assert payload["active_this_week"] >= 1
    assert payload["last_active_date"] is not None


def test_streak_counts_social_posts(client, auth_header):
    top = client.post(
        "/api/v1/closet/items",
        json={"name": "Post tee", "category": "Top"},
        headers=auth_header,
    ).json()
    client.post(
        "/api/v1/social/posts",
        data={"top_id": top["id"]},
        headers=auth_header,
    )
    streak = client.get("/api/v1/social/streak", headers=auth_header)
    assert streak.status_code == 200
    assert streak.json()["total_fit_days"] >= 1

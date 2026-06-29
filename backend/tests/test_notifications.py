from datetime import datetime, timezone
from unittest.mock import patch

from app.services.notification_service import NotificationService, plan_notification_text


def test_plan_notification_text_wear_and_pack():
    plan = {
        "activities": [
            {
                "mode": "wear",
                "title": "Work",
                "top": {"name": "Oxford shirt"},
                "bottom": {"name": "Slacks"},
            },
            {"mode": "pack", "title": "Gym"},
        ]
    }
    title, body = plan_notification_text(plan)
    assert title == "Your outfit for today"
    assert "Oxford shirt" in body
    assert "Pack for 1 stop" in body


def test_routines_due_at_wake_time(client, auth_header):
    client.put(
        "/api/v1/outfits/routine",
        json={
            "notifications_enabled": True,
            "wake_time": "09:15",
            "timezone": "UTC",
        },
        headers=auth_header,
    )
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        due = NotificationService.routines_due_now(
            db, now_utc=datetime(2026, 6, 29, 9, 15, tzinfo=timezone.utc)
        )
        assert len(due) >= 1
        assert due[0].wake_time == "09:15"
    finally:
        db.close()


def test_register_and_test_notification(client, auth_header):
    register = client.post(
        "/api/v1/notifications/register",
        json={"token": "ExponentPushToken[test-token-123]", "platform": "ios", "timezone": "UTC"},
        headers=auth_header,
    )
    assert register.status_code == 204

    with patch("app.services.notification_service.NotificationService.send_expo_push") as mock_send:
        mock_send.return_value = {"data": [{"status": "ok"}]}
        response = client.post("/api/v1/notifications/test", headers=auth_header)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Your outfit for today"
    assert mock_send.called


def test_morning_scheduler_marks_sent_once(client, auth_header):
    client.post(
        "/api/v1/notifications/register",
        json={"token": "ExponentPushToken[scheduler-token]", "platform": "ios", "timezone": "UTC"},
        headers=auth_header,
    )
    client.put(
        "/api/v1/outfits/routine",
        json={
            "notifications_enabled": True,
            "wake_time": "08:00",
            "timezone": "UTC",
            "weekday_activities": ["work"],
        },
        headers=auth_header,
    )
    client.post(
        "/api/v1/closet/items",
        json={"name": "Shirt", "category": "top", "occasion": ["work"], "is_clean": True},
        headers=auth_header,
    )

    now = datetime(2026, 6, 29, 8, 0, tzinfo=timezone.utc)
    with patch("app.services.notification_service.NotificationService.send_expo_push") as mock_send:
        mock_send.return_value = {"data": [{"status": "ok"}]}
        from app.database import SessionLocal

        db = SessionLocal()
        try:
            sent = NotificationService.process_morning_notifications(db, now_utc=now)
            assert sent == 1
            sent_again = NotificationService.process_morning_notifications(db, now_utc=now)
            assert sent_again == 0
        finally:
            db.close()

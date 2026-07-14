import hashlib
import hmac

from app.config import settings
from app.utils.mailgun import verify_mailgun_signature


def test_verify_mailgun_signature_accepts_valid_digest():
    signing_key = "test-signing-key"
    timestamp = "1700000000"
    token = "abc123"
    digest = hmac.new(
        key=signing_key.encode("utf-8"),
        msg=f"{timestamp}{token}".encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()
    assert verify_mailgun_signature(signing_key, timestamp, token, digest) is True


def test_verify_mailgun_signature_rejects_invalid_digest():
    assert verify_mailgun_signature("key", "1", "token", "bad") is False


def test_get_email_ingest_settings(client, auth_header, monkeypatch):
    monkeypatch.setattr(settings, "EMAIL_INGEST_ENABLED", True)
    monkeypatch.setattr(settings, "EMAIL_INGEST_DOMAIN", "ingest.example.com")

    response = client.get("/api/v1/closet/email-ingest", headers=auth_header)

    assert response.status_code == 200
    body = response.json()
    assert body["enabled"] is True
    assert body["address"].startswith("u-")
    assert body["address"].endswith("@ingest.example.com")


def test_simulate_email_ingest_creates_review_items(client, auth_header, monkeypatch):
    monkeypatch.setattr(settings, "EMAIL_INGEST_ENABLED", True)
    monkeypatch.setattr(settings, "EMAIL_INGEST_DOMAIN", "ingest.example.com")

    files = {"attachment": ("receipt.jpg", b"\xff\xd8\xff\xe0fake-receipt", "image/jpeg")}
    response = client.post("/api/v1/closet/email-ingest/simulate", files=files, headers=auth_header)

    assert response.status_code == 200
    body = response.json()
    assert body["items_created"] >= 1

    items = client.get("/api/v1/closet/items", headers=auth_header).json()
    email_items = [item for item in items if item["source"] == "email"]
    assert email_items
    # Stub receipt lines are high-confidence — silent add, no review badge.
    assert email_items[0]["needs_review"] is False


def test_email_flag_review_helper():
    from app.schemas.ingestion import DraftItem
    from app.services.email_ingest_service import EmailIngestService

    solid = DraftItem(
        name="Tee",
        category="top",
        brand="Uniqlo",
        confidence={"brand": 0.96, "category": 0.95},
        needs_review=False,
    )
    assert EmailIngestService._should_flag_review(solid) is False

    shaky = DraftItem(
        name="Mystery",
        category="top",
        color="black",
        confidence={"color": 0.4},
        needs_review=False,
    )
    assert EmailIngestService._should_flag_review(shaky) is True

    forced = DraftItem(name="X", category="top", needs_review=True)
    assert EmailIngestService._should_flag_review(forced) is True


def test_mailgun_webhook_creates_items(client, auth_header, monkeypatch):
    monkeypatch.setattr(settings, "EMAIL_INGEST_ENABLED", True)
    monkeypatch.setattr(settings, "EMAIL_INGEST_DOMAIN", "ingest.example.com")
    monkeypatch.setattr(settings, "ENV", "development")
    monkeypatch.setattr(settings, "MAILGUN_WEBHOOK_SIGNING_KEY", "")

    settings_response = client.get("/api/v1/closet/email-ingest", headers=auth_header)
    address = settings_response.json()["address"]

    response = client.post(
        "/api/v1/closet/email-ingest/webhook",
        data={
            "recipient": address,
            "sender": "orders@store.example",
            "subject": "Your Uniqlo receipt",
            "attachment-count": "1",
        },
        files=[("attachment-1", ("receipt.jpg", b"\xff\xd8\xff\xe0fake-receipt", "image/jpeg"))],
    )

    assert response.status_code == 200
    assert response.json()["items_created"] >= 1

    logs = client.get("/api/v1/closet/email-ingest/logs", headers=auth_header).json()
    assert len(logs) >= 1
    assert logs[0]["items_created"] >= 1


def test_mailgun_webhook_rejects_bad_signature_in_production(client, auth_header, monkeypatch):
    monkeypatch.setattr(settings, "EMAIL_INGEST_ENABLED", True)
    monkeypatch.setattr(settings, "EMAIL_INGEST_DOMAIN", "ingest.example.com")
    monkeypatch.setattr(settings, "ENV", "production")
    monkeypatch.setattr(settings, "MAILGUN_WEBHOOK_SIGNING_KEY", "real-key")

    settings_response = client.get("/api/v1/closet/email-ingest", headers=auth_header)
    address = settings_response.json()["address"]

    response = client.post(
        "/api/v1/closet/email-ingest/webhook",
        data={
            "recipient": address,
            "sender": "orders@store.example",
            "subject": "Receipt",
            "timestamp": "1",
            "token": "tok",
            "signature": "invalid",
            "attachment-count": "0",
        },
    )

    assert response.status_code == 403

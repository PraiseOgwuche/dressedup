from unittest.mock import MagicMock, patch

from app.config import settings
from app.services.storage import get_storage_provider
from app.services.storage.s3 import S3StorageProvider


def test_s3_save_uploads_and_returns_https_url(monkeypatch):
    monkeypatch.setattr(settings, "STORAGE_PROVIDER", "s3")
    monkeypatch.setattr(settings, "S3_BUCKET", "dressedup-media")
    monkeypatch.setattr(settings, "AWS_REGION", "us-east-1")
    monkeypatch.setattr(settings, "AWS_ACCESS_KEY_ID", "test-key")
    monkeypatch.setattr(settings, "AWS_SECRET_ACCESS_KEY", "test-secret")
    monkeypatch.setattr(settings, "S3_PUBLIC_BASE_URL", "")
    monkeypatch.setattr(settings, "S3_OBJECT_ACL", "")

    mock_client = MagicMock()
    with patch("app.services.storage.s3.boto3.client", return_value=mock_client):
        provider = S3StorageProvider()
        url = provider.save(b"\xff\xd8\xff\xe0img", ext="jpg", subdir="items")

    mock_client.put_object.assert_called_once()
    call = mock_client.put_object.call_args.kwargs
    assert call["Bucket"] == "dressedup-media"
    assert call["Key"].startswith("items/")
    assert call["Key"].endswith(".jpg")
    assert call["ContentType"] == "image/jpeg"
    assert "ACL" not in call
    assert url == f"https://dressedup-media.s3.amazonaws.com/{call['Key']}"


def test_s3_public_base_url_override(monkeypatch):
    monkeypatch.setattr(settings, "S3_BUCKET", "dressedup-media")
    monkeypatch.setattr(settings, "AWS_REGION", "us-west-2")
    monkeypatch.setattr(settings, "S3_PUBLIC_BASE_URL", "https://cdn.example.com")
    monkeypatch.setattr(settings, "AWS_ACCESS_KEY_ID", "k")
    monkeypatch.setattr(settings, "AWS_SECRET_ACCESS_KEY", "s")

    mock_client = MagicMock()
    with patch("app.services.storage.s3.boto3.client", return_value=mock_client):
        provider = S3StorageProvider()
        url = provider.save(b"png", ext="png", subdir="items")

    key = mock_client.put_object.call_args.kwargs["Key"]
    assert url == f"https://cdn.example.com/{key}"


def test_get_storage_provider_selects_s3(monkeypatch):
    monkeypatch.setattr(settings, "STORAGE_PROVIDER", "s3")
    monkeypatch.setattr(settings, "S3_BUCKET", "dressedup-media")
    monkeypatch.setattr(settings, "AWS_ACCESS_KEY_ID", "k")
    monkeypatch.setattr(settings, "AWS_SECRET_ACCESS_KEY", "s")

    with patch("app.services.storage.s3.boto3.client", return_value=MagicMock()):
        provider = get_storage_provider()
    assert isinstance(provider, S3StorageProvider)

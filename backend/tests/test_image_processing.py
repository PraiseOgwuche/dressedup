import io

from PIL import Image

from app.config import settings
from app.services import image_processing
from app.services.image_processing import remove_background


def _png_bytes(size=(64, 64), color=(200, 50, 50)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, color).save(buffer, format="PNG")
    return buffer.getvalue()


def test_disabled_flag_returns_none(monkeypatch):
    monkeypatch.setattr(settings, "BG_REMOVAL_ENABLED", False)
    assert remove_background(_png_bytes()) is None


def test_invalid_image_bytes_return_none(monkeypatch):
    monkeypatch.setattr(settings, "BG_REMOVAL_ENABLED", True)
    assert remove_background(b"\xff\xd8\xff\xe0not-really-an-image") is None


def test_rembg_failure_returns_none(monkeypatch):
    """If the ML session can't be created, valid images still pass through."""
    monkeypatch.setattr(settings, "BG_REMOVAL_ENABLED", True)
    monkeypatch.setattr(image_processing, "_get_session", lambda: None)
    assert remove_background(_png_bytes()) is None


def test_ingest_falls_back_to_original_when_cutout_unavailable(client, auth_header, monkeypatch):
    """End-to-end: fake image bytes can't be segmented, so thumbnail_url must
    equal image_url (never null, never an error)."""
    files = {"garment": ("tee.jpg", b"\xff\xd8\xff\xe0fake-image", "image/jpeg")}
    response = client.post("/api/v1/closet/ingest", files=files, headers=auth_header)

    assert response.status_code == 200
    body = response.json()
    assert body["thumbnail_url"] == body["image_url"]


def test_ingest_uses_cutout_when_available(client, auth_header, monkeypatch):
    """When segmentation succeeds, thumbnail_url points at a cutout PNG."""
    cutout = _png_bytes(size=(32, 32), color=(10, 120, 200))
    monkeypatch.setattr(
        "app.services.ingestion_service.remove_background",
        lambda _data: cutout,
    )
    files = {"garment": ("tee.jpg", b"\xff\xd8\xff\xe0fake-image", "image/jpeg")}
    response = client.post("/api/v1/closet/ingest", files=files, headers=auth_header)

    assert response.status_code == 200
    body = response.json()
    assert body["thumbnail_url"] != body["image_url"]
    assert "/cutouts/" in body["thumbnail_url"]
    assert body["thumbnail_url"].endswith(".png")

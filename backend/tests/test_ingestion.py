from app.config import settings
from app.schemas.ingestion import DraftItem
from app.services.vision import get_vision_provider
from app.services.vision.stub import StubVisionProvider
from app.taxonomy import CATEGORIES


def test_factory_falls_back_to_stub_without_key(monkeypatch):
    monkeypatch.setattr(settings, "VISION_PROVIDER", "anthropic")
    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "")
    assert isinstance(get_vision_provider(), StubVisionProvider)


def test_anthropic_provider_module_imports():
    # Imports anthropic + PIL and validates the tool schema is taxonomy-bound,
    # without making any API call.
    from app.services.vision.anthropic_provider import AnthropicVisionProvider, _TOOL

    assert AnthropicVisionProvider is not None
    category_enum = _TOOL["input_schema"]["properties"]["category"]["enum"]
    assert "top" in category_enum and "jewelry" in category_enum


def test_stub_returns_valid_draft_without_label():
    draft = get_vision_provider().extract_attributes(garment_image=b"fake-image")

    assert isinstance(draft, DraftItem)
    assert draft.category in CATEGORIES
    assert draft.confidence.get("category", 0) > 0.5
    # Identity is unknown from a garment photo alone.
    assert draft.brand is None
    assert draft.needs_review is True
    assert draft.source == "photo"


def test_stub_label_image_adds_identity():
    draft = get_vision_provider().extract_attributes(
        garment_image=b"fake-image", label_image=b"fake-label"
    )

    assert draft.brand is not None
    assert draft.material is not None
    assert draft.source == "label_ocr"
    assert draft.needs_review is False


def test_ingest_endpoint_returns_draft_and_image(client, auth_header):
    files = {"garment": ("tee.jpg", b"\xff\xd8\xff\xe0fake-image", "image/jpeg")}
    response = client.post("/api/v1/closet/ingest", files=files, headers=auth_header)

    assert response.status_code == 200
    body = response.json()
    assert body["image_url"].startswith("/media/")
    assert body["draft"]["category"] in CATEGORIES
    assert body["draft"]["brand"] is None  # no label image


def test_ingest_batch_returns_entry_per_image(client, auth_header):
    files = [
        ("garments", ("a.jpg", b"\xff\xd8\xff\xe0img-a", "image/jpeg")),
        ("garments", ("b.jpg", b"\xff\xd8\xff\xe0img-b", "image/jpeg")),
        ("garments", ("notes.txt", b"hello", "text/plain")),  # rejected per-item
    ]
    response = client.post("/api/v1/closet/ingest/batch", files=files, headers=auth_header)

    assert response.status_code == 200
    entries = response.json()["entries"]
    assert len(entries) == 3
    ok = [e for e in entries if e["result"]]
    bad = [e for e in entries if e["error"]]
    assert len(ok) == 2 and len(bad) == 1
    assert ok[0]["result"]["draft"]["category"] in CATEGORIES


def test_ingest_batch_rejects_oversized_batch(client, auth_header):
    files = [("garments", (f"{i}.jpg", b"\xff\xd8\xff\xe0x", "image/jpeg")) for i in range(16)]
    response = client.post("/api/v1/closet/ingest/batch", files=files, headers=auth_header)

    assert response.status_code == 400


def test_stub_multi_returns_several_items():
    drafts = get_vision_provider().extract_multi_attributes(garment_image=b"fake-flatlay")
    assert len(drafts) >= 2
    categories = {d.category for d in drafts}
    assert "top" in categories or "bottom" in categories


def test_ingest_multi_endpoint_returns_entries(client, auth_header):
    files = {"garment": ("flatlay.jpg", b"\xff\xd8\xff\xe0fake-flatlay", "image/jpeg")}
    response = client.post("/api/v1/closet/ingest/multi", files=files, headers=auth_header)

    assert response.status_code == 200
    body = response.json()
    assert body["source_image_url"].startswith("/media/")
    assert len(body["entries"]) >= 2
    assert body["entries"][0]["draft"]["category"] in CATEGORIES


def test_ingest_endpoint_rejects_non_image(client, auth_header):
    files = {"garment": ("notes.txt", b"hello", "text/plain")}
    response = client.post("/api/v1/closet/ingest", files=files, headers=auth_header)

    assert response.status_code == 415


def test_confirm_persists_provenance(client, auth_header):
    response = client.post(
        "/api/v1/closet/items",
        json={
            "name": "Black tee",
            "category": "top",
            "image_url": "/media/items/abc.jpg",
            "source": "photo",
            "needs_review": True,
        },
        headers=auth_header,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["source"] == "photo"
    assert body["image_url"] == "/media/items/abc.jpg"
    assert body["needs_review"] is True

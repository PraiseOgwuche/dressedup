"""Outfit Engine v4 Phase 3 — embeddings at ingest time + backfill semantics."""

import uuid
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

from app.config import settings
from app.models.user import User
from app.schemas.closet import ClothingItemCreate, ClothingItemUpdate
from app.services.closet_service import ClosetService
from app.services.embedding_service import (
    STATUS_FAILED,
    STATUS_PENDING,
    STATUS_READY,
    STATUS_SKIPPED,
    EmbeddingService,
)


@pytest.fixture
def user(db_session):
    row = User(
        email=f"embed-ingest-{uuid.uuid4().hex[:8]}@example.com",
        full_name="Embed Ingest",
        hashed_password="x",
    )
    db_session.add(row)
    db_session.commit()
    return row


@pytest.fixture
def embeddings_on(monkeypatch):
    monkeypatch.setattr(settings, "OUTFIT_EMBEDDINGS_ENABLED", True)


def _stored_image_url(color=(180, 40, 40)) -> str:
    """Write a real PNG under MEDIA_DIR so fetch_stored_image_bytes can read it."""
    name = f"{uuid.uuid4().hex}.png"
    path = Path(settings.MEDIA_DIR) / "items" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    buffer = BytesIO()
    Image.new("RGB", (64, 64), color).save(buffer, format="PNG")
    path.write_bytes(buffer.getvalue())
    return f"{settings.MEDIA_URL_PREFIX}/items/{name}"


def _create(db, user, **overrides):
    payload = ClothingItemCreate(name="Tee", category="top", **overrides)
    return ClosetService.create_item(db, user.id, payload)


def test_create_item_stays_pending_while_flag_off(db_session, user):
    item = _create(db_session, user, image_url=_stored_image_url())
    assert item.embedding is None
    assert item.embedding_status == STATUS_PENDING


def test_create_item_embeds_automatically(db_session, user, embeddings_on):
    item = _create(db_session, user, image_url=_stored_image_url())
    assert item.embedding_status == STATUS_READY
    assert item.embedding is not None and len(item.embedding) == 512
    assert item.embedding_model == "stub"
    assert item.embedded_at is not None
    assert item.embedding_error is None


def test_create_item_without_image_is_skipped(db_session, user, embeddings_on):
    item = _create(db_session, user)
    assert item.embedding_status == STATUS_SKIPPED
    assert item.embedding_error == "no_image"
    assert item.embedding is None


def test_unreadable_image_marks_failed_then_retry_succeeds(db_session, user, embeddings_on):
    item = _create(db_session, user, image_url="/media/items/does-not-exist.png")
    assert item.embedding_status == STATUS_FAILED
    assert item.embedding_error == "image_unreadable"

    # Failure never blocks the closet: the item row itself was created fine.
    assert item.id is not None

    item.image_url = _stored_image_url()
    assert EmbeddingService.embed_item(db_session, item) is True
    assert item.embedding_status == STATUS_READY
    assert item.embedding_error is None


def test_photo_replacement_re_embeds(db_session, user, embeddings_on):
    item = _create(db_session, user, image_url=_stored_image_url((180, 40, 40)))
    original_vector = list(item.embedding)

    updated = ClosetService.update_item(
        db_session,
        user.id,
        item.id,
        ClothingItemUpdate(image_url=_stored_image_url((30, 60, 200))),
    )
    assert updated.embedding_status == STATUS_READY
    assert list(updated.embedding) != original_vector


def test_non_photo_update_keeps_embedding(db_session, user, embeddings_on):
    item = _create(db_session, user, image_url=_stored_image_url())
    vector = list(item.embedding)
    embedded_at = item.embedded_at

    updated = ClosetService.update_item(
        db_session, user.id, item.id, ClothingItemUpdate(name="Renamed Tee")
    )
    assert updated.embedding_status == STATUS_READY
    assert list(updated.embedding) == vector
    assert updated.embedded_at == embedded_at


def test_cutout_prefers_thumbnail_over_original(db_session, user, embeddings_on):
    original = _stored_image_url((10, 10, 10))
    cutout = _stored_image_url((240, 240, 240))
    with_thumb = _create(db_session, user, image_url=original, thumbnail_url=cutout)
    without_thumb = _create(db_session, user, image_url=original)
    # Stub provider hashes the raw bytes, so different source image -> different vector.
    assert list(with_thumb.embedding) != list(without_thumb.embedding)


def test_mark_stale_resets_all_embedding_fields(db_session, user, embeddings_on):
    item = _create(db_session, user, image_url=_stored_image_url())
    EmbeddingService.mark_stale(item)
    assert item.embedding is None
    assert item.embedding_model is None
    assert item.embedding_version is None
    assert item.embedding_status == STATUS_PENDING
    assert item.embedded_at is None


def test_is_stale_detects_model_version_change(db_session, user, embeddings_on):
    item = _create(db_session, user, image_url=_stored_image_url())
    assert EmbeddingService.is_stale(item) is False
    item.embedding_version = "0-old"
    assert EmbeddingService.is_stale(item) is True

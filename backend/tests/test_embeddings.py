"""Outfit Engine v4 Phases 1–2 — embedding foundation contract tests."""

import math
from io import BytesIO
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from app.config import settings
from app.models.clothing_item import ClothingItem
from app.models.types import EMBEDDING_DIM
from app.models.user import User
from app.services.embedding import StubEmbeddingProvider, get_embedding_provider
from app.services.embedding.fashionclip_provider import (
    VISION_MODEL_FILENAME,
    FashionClipEmbeddingProvider,
    preprocess_image,
)

_MODEL_PATH = Path(settings.EMBEDDING_MODEL_DIR) / VISION_MODEL_FILENAME


def _png_bytes(color, size=(300, 400), mode="RGB") -> bytes:
    buffer = BytesIO()
    Image.new(mode, size, color).save(buffer, format="PNG")
    return buffer.getvalue()


def _unit_length(vector: list[float]) -> float:
    return math.sqrt(sum(value * value for value in vector))


def test_embeddings_are_disabled_by_default():
    assert settings.OUTFIT_EMBEDDINGS_ENABLED is False
    assert settings.EMBEDDING_PROVIDER == "stub"


def test_factory_defaults_to_stub():
    provider = get_embedding_provider()
    assert isinstance(provider, StubEmbeddingProvider)
    assert provider.dim == EMBEDDING_DIM


def test_stub_embedding_contract():
    provider = StubEmbeddingProvider()
    first = provider.embed_image(b"garment-photo-bytes")
    second = provider.embed_image(b"garment-photo-bytes")
    other = provider.embed_image(b"different-photo-bytes")

    assert len(first) == EMBEDDING_DIM
    assert first == second  # byte-identical input -> identical vector
    assert first != other
    assert abs(_unit_length(first) - 1.0) < 1e-9


def test_embedding_columns_roundtrip(db_session):
    user = User(
        email="embedding-roundtrip@example.com",
        full_name="Embedding Tester",
        hashed_password="x",
    )
    db_session.add(user)
    db_session.flush()

    vector = StubEmbeddingProvider().embed_image(b"roundtrip")
    item = ClothingItem(
        user_id=user.id,
        name="Vector Tee",
        category="top",
        embedding=vector,
        embedding_model="stub",
        embedding_version="1",
        embedding_status="ready",
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)

    assert list(item.embedding) == vector
    assert item.embedding_model == "stub"
    assert item.embedding_status == "ready"


def test_preprocess_produces_clip_tensor():
    tensor = preprocess_image(_png_bytes((30, 90, 180)))
    assert tensor.shape == (1, 3, 224, 224)
    assert tensor.dtype == np.float32
    assert np.isfinite(tensor).all()


def test_preprocess_composites_transparency_onto_white():
    # Fully transparent cutout must preprocess like a white product background,
    # not black — rembg cutouts are RGBA PNGs.
    transparent = preprocess_image(_png_bytes((0, 0, 0, 0), mode="RGBA"))
    white = preprocess_image(_png_bytes((255, 255, 255)))
    assert np.allclose(transparent, white, atol=1e-5)


def test_preprocess_handles_non_square_images():
    wide = preprocess_image(_png_bytes((120, 40, 40), size=(900, 300)))
    tall = preprocess_image(_png_bytes((120, 40, 40), size=(300, 900)))
    assert wide.shape == tall.shape == (1, 3, 224, 224)


def test_factory_falls_back_to_stub_when_weights_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "EMBEDDING_PROVIDER", "fashionclip")
    monkeypatch.setattr(settings, "EMBEDDING_MODEL_DIR", str(tmp_path / "missing"))
    provider = get_embedding_provider()
    assert isinstance(provider, StubEmbeddingProvider)


@pytest.mark.skipif(not _MODEL_PATH.exists(), reason="FashionCLIP weights not downloaded")
def test_fashionclip_real_model_contract():
    provider = FashionClipEmbeddingProvider()
    shirt_like = provider.embed_image(_png_bytes((200, 30, 30)))
    shirt_like_again = provider.embed_image(_png_bytes((200, 30, 30)))
    other = provider.embed_image(_png_bytes((20, 40, 90), size=(500, 200)))

    assert len(shirt_like) == EMBEDDING_DIM
    assert abs(_unit_length(shirt_like) - 1.0) < 1e-5
    assert shirt_like == shirt_like_again  # deterministic
    assert shirt_like != other


def test_embedding_status_defaults_to_pending(db_session):
    user = User(
        email="embedding-default@example.com",
        full_name="Embedding Default",
        hashed_password="x",
    )
    db_session.add(user)
    db_session.flush()

    item = ClothingItem(user_id=user.id, name="Plain Tee", category="top")
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)

    assert item.embedding is None
    assert item.embedding_status == "pending"
    assert item.embedded_at is None

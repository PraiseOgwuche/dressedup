"""Outfit Engine v4 Phase 1 — vector foundation contract tests."""

import math

from app.config import settings
from app.models.clothing_item import ClothingItem
from app.models.types import EMBEDDING_DIM
from app.models.user import User
from app.services.embedding import StubEmbeddingProvider, get_embedding_provider


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

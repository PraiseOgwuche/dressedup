"""Outfit Engine v4 Phase 3 — compute and store garment embeddings.

Embedding happens at ingest/backfill time (never in the suggestion hot path)
and must never break closet operations: every failure lands in
`embedding_status` / `embedding_error` instead of raising.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.models.clothing_item import ClothingItem
from app.services.embedding import get_embedding_provider
from app.services.image_processing import fetch_stored_image_bytes

logger = logging.getLogger(__name__)

STATUS_PENDING = "pending"
STATUS_READY = "ready"
STATUS_FAILED = "failed"
STATUS_SKIPPED = "skipped"


class EmbeddingService:
    @staticmethod
    def _image_url(item: ClothingItem) -> str | None:
        """Prefer the rembg cutout (clean background) over the raw photo."""
        return item.thumbnail_url or item.image_url

    @staticmethod
    def mark_stale(item: ClothingItem) -> None:
        """Reset embedding state after the item's photo changes."""
        item.embedding = None
        item.embedding_model = None
        item.embedding_version = None
        item.embedding_status = STATUS_PENDING
        item.embedded_at = None
        item.embedding_error = None

    @staticmethod
    def embed_item(db: Session, item: ClothingItem, *, commit: bool = True) -> bool:
        """Compute + persist the embedding for one item. Returns True when ready.

        No-op while OUTFIT_EMBEDDINGS_ENABLED is false. Never raises.
        """
        if not settings.OUTFIT_EMBEDDINGS_ENABLED:
            return False

        url = EmbeddingService._image_url(item)
        if not url:
            item.embedding_status = STATUS_SKIPPED
            item.embedding_error = "no_image"
        else:
            data = fetch_stored_image_bytes(url)
            if data is None:
                item.embedding_status = STATUS_FAILED
                item.embedding_error = "image_unreadable"
            else:
                provider = get_embedding_provider()
                try:
                    item.embedding = provider.embed_image(data)
                except Exception as exc:  # noqa: BLE001 — recorded, retried by backfill
                    logger.exception("Embedding failed for item %s", item.id)
                    item.embedding_status = STATUS_FAILED
                    item.embedding_error = str(exc)[:500] or "embed_failed"
                else:
                    item.embedding_model = provider.model_name
                    item.embedding_version = provider.model_version
                    item.embedding_status = STATUS_READY
                    item.embedded_at = datetime.now(timezone.utc)
                    item.embedding_error = None

        db.add(item)
        if commit:
            db.commit()
        return item.embedding_status == STATUS_READY

    @staticmethod
    def is_stale(item: ClothingItem) -> bool:
        """True when the stored vector was produced by a different model/version."""
        if item.embedding_status != STATUS_READY:
            return False
        provider = get_embedding_provider()
        return (
            item.embedding_model != provider.model_name
            or item.embedding_version != provider.model_version
        )

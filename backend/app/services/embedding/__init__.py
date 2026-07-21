import logging

from app.config import settings
from app.services.embedding.base import EmbeddingProvider
from app.services.embedding.stub import StubEmbeddingProvider

logger = logging.getLogger(__name__)


def get_embedding_provider() -> EmbeddingProvider:
    """Resolve the configured provider.

    Defaults to the free deterministic stub. "fashionclip" (Phase 2) is
    imported lazily so ONNX Runtime and model weights stay off the default
    path; misconfiguration falls back to the stub rather than crashing ingest.
    """
    if settings.EMBEDDING_PROVIDER == "fashionclip":
        try:
            from app.services.embedding.fashionclip_provider import FashionClipEmbeddingProvider

            return FashionClipEmbeddingProvider()
        except Exception:  # noqa: BLE001 — never let embedding config break ingestion
            logger.exception("EMBEDDING_PROVIDER=fashionclip unavailable; using stub.")
            return StubEmbeddingProvider()

    return StubEmbeddingProvider()


__all__ = ["EmbeddingProvider", "StubEmbeddingProvider", "get_embedding_provider"]

from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """Turns a garment image into a fixed-size style vector.

    Implementations stay behind this contract so ingestion, backfill, and
    retrieval can be built/tested against the deterministic stub, then swapped
    for the real FashionCLIP encoder (Phase 2) without touching callers.

    Contract:
    - `embed_image` returns a list of exactly `dim` floats, L2-normalized
      (unit length), so cosine similarity reduces to a dot product.
    - Identical bytes must produce identical vectors (idempotent backfill).
    """

    #: Reported in `clothing_items.embedding_model` for provenance.
    model_name: str
    #: Bumped when the model/preprocessing changes; triggers re-embedding.
    model_version: str
    dim: int = 512

    @abstractmethod
    def embed_image(self, image_bytes: bytes) -> list[float]:
        """Return the unit-length embedding for one garment image."""
        raise NotImplementedError

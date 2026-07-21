import hashlib
import math
import random

from app.services.embedding.base import EmbeddingProvider


class StubEmbeddingProvider(EmbeddingProvider):
    """Deterministic, free embedding for tests and development.

    Hashes the image bytes into a PRNG seed and emits a stable unit vector.
    Not semantically meaningful — it only guarantees the pipeline contract:
    fixed dimension, unit length, and byte-identical determinism.
    """

    model_name = "stub"
    model_version = "1"
    dim = 512

    def embed_image(self, image_bytes: bytes) -> list[float]:
        seed = int.from_bytes(hashlib.sha256(image_bytes).digest()[:8], "big")
        rng = random.Random(seed)
        raw = [rng.gauss(0.0, 1.0) for _ in range(self.dim)]
        norm = math.sqrt(sum(value * value for value in raw)) or 1.0
        return [value / norm for value in raw]

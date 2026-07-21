"""Cross-dialect column types."""

from __future__ import annotations

from sqlalchemy import JSON
from sqlalchemy.types import TypeDecorator

EMBEDDING_DIM = 512


class EmbeddingVector(TypeDecorator):
    """pgvector `vector(N)` on Postgres, JSON list of floats elsewhere (SQLite tests).

    Values are plain Python lists in application code either way; pgvector may
    return numpy arrays on Postgres, which compare fine after `list()`.
    """

    impl = JSON
    cache_ok = True

    def __init__(self, dim: int = EMBEDDING_DIM):
        super().__init__()
        self.dim = dim

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from pgvector.sqlalchemy import Vector

            return dialect.type_descriptor(Vector(self.dim))
        return dialect.type_descriptor(JSON())

"""0017 clothing item embeddings (Outfit Engine v4 Phase 1)

Adds the pgvector extension (Postgres only), a 512-dim embedding column, and
embedding provenance/status metadata. Additive and nullable — no behavior
change while OUTFIT_EMBEDDINGS_ENABLED is false.

Revision ID: 0017_item_embeddings
Revises: 0016_clothing_tags
Create Date: 2026-07-20 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0017_item_embeddings"
down_revision: Union[str, None] = "0016_clothing_tags"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EMBEDDING_DIM = 512


def _is_postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    if _is_postgres():
        from pgvector.sqlalchemy import Vector

        op.execute("CREATE EXTENSION IF NOT EXISTS vector")
        embedding_type: sa.types.TypeEngine = Vector(EMBEDDING_DIM)
    else:
        embedding_type = sa.JSON()

    op.add_column("clothing_items", sa.Column("embedding", embedding_type, nullable=True))
    op.add_column("clothing_items", sa.Column("embedding_model", sa.String(), nullable=True))
    op.add_column("clothing_items", sa.Column("embedding_version", sa.String(), nullable=True))
    op.add_column(
        "clothing_items",
        sa.Column("embedding_status", sa.String(), nullable=False, server_default="pending"),
    )
    op.add_column(
        "clothing_items",
        sa.Column("embedded_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column("clothing_items", sa.Column("embedding_error", sa.String(), nullable=True))
    op.create_index(
        "ix_clothing_items_embedding_status",
        "clothing_items",
        ["embedding_status"],
    )


def downgrade() -> None:
    op.drop_index("ix_clothing_items_embedding_status", table_name="clothing_items")
    op.drop_column("clothing_items", "embedding_error")
    op.drop_column("clothing_items", "embedded_at")
    op.drop_column("clothing_items", "embedding_status")
    op.drop_column("clothing_items", "embedding_version")
    op.drop_column("clothing_items", "embedding_model")
    op.drop_column("clothing_items", "embedding")
    # The vector extension is left installed; other tables may adopt it.

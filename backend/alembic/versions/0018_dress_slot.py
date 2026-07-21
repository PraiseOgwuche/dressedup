"""0018 dress slot on feedback + signals (Outfit Engine v4 Phase 6)

Full-body garments (dresses/jumpsuits) become a first-class outfit slot, so
likes/wears/swaps must be attributable to the dress. Additive and nullable.

Revision ID: 0018_dress_slot
Revises: 0017_item_embeddings
Create Date: 2026-07-20 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0018_dress_slot"
down_revision: Union[str, None] = "0017_item_embeddings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "outfit_feedback",
        sa.Column("dress_id", sa.Integer(), sa.ForeignKey("clothing_items.id"), nullable=True),
    )
    op.add_column(
        "style_signals",
        sa.Column("dress_id", sa.Integer(), sa.ForeignKey("clothing_items.id"), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("style_signals", "dress_id")
    op.drop_column("outfit_feedback", "dress_id")

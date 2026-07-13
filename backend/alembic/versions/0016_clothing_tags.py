"""0016 clothing item capsule tags

Revision ID: 0016_clothing_tags
Revises: 0015_listing_interests
Create Date: 2026-07-12 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0016_clothing_tags"
down_revision: Union[str, None] = "0015_listing_interests"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("clothing_items", sa.Column("tags", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("clothing_items", "tags")
